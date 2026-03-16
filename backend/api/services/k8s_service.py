"""
Kubernetes service for managing Claw deployments
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def _get_apps_v1_api():
    """Load kubeconfig and return AppsV1Api client."""
    from kubernetes import client, config

    kubeconfig_path = os.getenv("KUBECONFIG_PATH", os.path.expanduser("~/.kube/config"))
    try:
        config.load_kube_config(config_file=kubeconfig_path)
    except Exception:
        # Fall back to in-cluster config (when running inside a pod)
        config.load_incluster_config()
    return client.AppsV1Api()


def _get_core_v1_api():
    """Load kubeconfig and return CoreV1Api client."""
    from kubernetes import client, config

    kubeconfig_path = os.getenv("KUBECONFIG_PATH", os.path.expanduser("~/.kube/config"))
    try:
        config.load_kube_config(config_file=kubeconfig_path)
    except Exception:
        config.load_incluster_config()
    return client.CoreV1Api()


def create_config_map(claw_id: int, config_files: dict, namespace: str = "default") -> str:
    """
    Create a K8s ConfigMap named claw-{claw_id}-config.
    config_files is a dict mapping filename -> file content; each key becomes a
    file mounted under /config inside the Pod.
    Returns the ConfigMap name on success.
    """
    from kubernetes import client

    configmap_name = f"claw-{claw_id}-config"
    core_v1 = _get_core_v1_api()
    configmap = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=configmap_name, namespace=namespace),
        data=config_files,
    )
    core_v1.create_namespaced_config_map(namespace=namespace, body=configmap)
    logger.info(f"Created K8s ConfigMap: {configmap_name} in namespace {namespace}")
    return configmap_name


def create_deployment(
    claw_id: int,
    image: str,
    config_files: dict,
    command: Optional[list] = None,
    user_email: str = "",
    namespace: str = "default",
) -> str:
    """
    1. Create a ConfigMap claw-{claw_id}-config from config_files dict.
    2. Build a V1Deployment directly (no template file), mounting the entire
       ConfigMap into /config inside the container.
    3. command (optional) overrides the container entrypoint.
    Cleans up the ConfigMap if Deployment creation fails.
    """
    from kubernetes import client

    deployment_name = f"claw-{claw_id}"
    configmap_name = create_config_map(claw_id, config_files, namespace)

    try:
        volume = client.V1Volume(
            name="config-volume",
            config_map=client.V1ConfigMapVolumeSource(name=configmap_name),
        )
        volume_mount = client.V1VolumeMount(
            name="config-volume",
            mount_path="/config",
        )
        container = client.V1Container(
            name="claw",
            image=image,
            command=command,
            volume_mounts=[volume_mount],
        )
        pod_spec = client.V1PodSpec(
            containers=[container],
            volumes=[volume],
            restart_policy="Always",
        )
        pod_template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
            spec=pod_spec,
        )
        deployment_spec = client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"app": deployment_name}),
            template=pod_template,
        )
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=deployment_name,
                namespace=namespace,
                annotations={"user-email": user_email},
            ),
            spec=deployment_spec,
        )
        apps_v1 = _get_apps_v1_api()
        apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
        logger.info(f"Created K8s Deployment: {deployment_name} in namespace {namespace}")
        return deployment_name
    except Exception:
        # Clean up ConfigMap if Deployment creation failed
        try:
            delete_config_map(configmap_name, namespace)
        except Exception as cleanup_err:
            logger.warning(f"Failed to clean up ConfigMap {configmap_name}: {cleanup_err}")
        raise


def delete_config_map(configmap_name: str, namespace: str = "default") -> None:
    """
    Delete a K8s ConfigMap by name. Silently ignores 404.
    """
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    core_v1 = _get_core_v1_api()
    try:
        core_v1.delete_namespaced_config_map(
            name=configmap_name,
            namespace=namespace,
            body=client.V1DeleteOptions(propagation_policy="Foreground"),
        )
        logger.info(f"Deleted K8s ConfigMap: {configmap_name} in namespace {namespace}")
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"K8s ConfigMap {configmap_name} not found, skipping deletion")
        else:
            logger.error(f"Failed to delete K8s ConfigMap {configmap_name}: {e}")
            raise


def delete_deployment(deployment_name: str, namespace: str = "default") -> None:
    """
    Delete a K8s Deployment by name.

    Silently ignores 404 (already deleted). Logs and raises on other errors.
    """
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    apps_v1 = _get_apps_v1_api()
    try:
        apps_v1.delete_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=client.V1DeleteOptions(propagation_policy="Foreground"),
        )
        logger.info(f"Deleted K8s Deployment: {deployment_name} in namespace {namespace}")
        delete_config_map(f"{deployment_name}-config", namespace)
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"K8s Deployment {deployment_name} not found, skipping deletion")
        else:
            logger.error(f"Failed to delete K8s Deployment {deployment_name}: {e}")
            raise

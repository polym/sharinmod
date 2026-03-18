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
            image_pull_policy="IfNotPresent",
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


def create_headless_service(claw_id: int, namespace: str = "default") -> str:
    """Create a headless Service for StatefulSet claw-{claw_id}."""
    from kubernetes import client

    svc_name = f"claw-{claw_id}"
    core_v1 = _get_core_v1_api()
    svc = client.V1Service(
        metadata=client.V1ObjectMeta(name=svc_name, namespace=namespace),
        spec=client.V1ServiceSpec(
            cluster_ip="None",  # headless
            selector={"app": svc_name},
            ports=[client.V1ServicePort(port=80, name="placeholder")],
        ),
    )
    core_v1.create_namespaced_service(namespace=namespace, body=svc)
    logger.info(f"Created headless Service: {svc_name}")
    return svc_name


def create_statefulset(
    claw_id: int,
    image: str,
    config_files: dict,
    command: Optional[list] = None,
    user_email: str = "",
    namespace: str = "default",
) -> str:
    """
    Create: ConfigMap + Headless Service + StatefulSet (with workspace PVC).
    Returns StatefulSet name on success. Rolls back on failure.
    """
    import yaml as _yaml
    from kubernetes import client
    from api.config import _get_config_path

    # 读取存储配置
    config_path = _get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        root_cfg = _yaml.safe_load(f)
    storage_class = root_cfg.get("workspace_storage_class", "")
    storage_size = root_cfg.get("workspace_storage_size", "10Gi")

    sts_name = f"claw-{claw_id}"
    configmap_name = create_config_map(claw_id, config_files, namespace)
    svc_created = False

    try:
        create_headless_service(claw_id, namespace)
        svc_created = True

        volume_config = client.V1Volume(
            name="config-volume",
            config_map=client.V1ConfigMapVolumeSource(name=configmap_name),
        )
        volume_mounts = [
            client.V1VolumeMount(name="config-volume", mount_path="/config"),
            client.V1VolumeMount(name="workspace-data", mount_path="/app/workspace"),
        ]
        container = client.V1Container(
            name="claw",
            image=image,
            image_pull_policy="IfNotPresent",
            command=command,
            volume_mounts=volume_mounts,
        )
        pvc_spec = client.V1PersistentVolumeClaimSpec(
            access_modes=["ReadWriteOnce"],
            resources=client.V1ResourceRequirements(requests={"storage": storage_size}),
        )
        if storage_class:
            pvc_spec.storage_class_name = storage_class
        pvc_template = client.V1PersistentVolumeClaim(
            metadata=client.V1ObjectMeta(name="workspace-data"),
            spec=pvc_spec,
        )
        sts_spec = client.V1StatefulSetSpec(
            service_name=sts_name,
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"app": sts_name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": sts_name}),
                spec=client.V1PodSpec(
                    containers=[container],
                    volumes=[volume_config],
                    restart_policy="Always",
                ),
            ),
            volume_claim_templates=[pvc_template],
        )
        sts = client.V1StatefulSet(
            metadata=client.V1ObjectMeta(
                name=sts_name,
                namespace=namespace,
                annotations={"user-email": user_email},
            ),
            spec=sts_spec,
        )
        apps_v1 = _get_apps_v1_api()
        apps_v1.create_namespaced_stateful_set(namespace=namespace, body=sts)
        logger.info(f"Created K8s StatefulSet: {sts_name}")
        return sts_name
    except Exception:
        if svc_created:
            try:
                _get_core_v1_api().delete_namespaced_service(sts_name, namespace)
            except Exception as e:
                logger.warning(f"Rollback: failed to delete headless Service {sts_name}: {e}")
        try:
            delete_config_map(configmap_name, namespace)
        except Exception as e:
            logger.warning(f"Rollback: failed to delete ConfigMap {configmap_name}: {e}")
        raise


def delete_statefulset(sts_name: str, namespace: str = "default") -> None:
    """Delete StatefulSet, its headless Service, PVC, and ConfigMap. Ignores 404."""
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    apps_v1 = _get_apps_v1_api()
    core_v1 = _get_core_v1_api()
    delete_opts = client.V1DeleteOptions(propagation_policy="Foreground")

    # 1. Delete StatefulSet
    try:
        apps_v1.delete_namespaced_stateful_set(sts_name, namespace, body=delete_opts)
        logger.info(f"Deleted StatefulSet: {sts_name}")
    except ApiException as e:
        if e.status != 404:
            logger.error(f"Failed to delete StatefulSet {sts_name}: {e}")
            raise

    # 2. Delete Headless Service
    try:
        core_v1.delete_namespaced_service(sts_name, namespace, body=delete_opts)
        logger.info(f"Deleted headless Service: {sts_name}")
    except ApiException as e:
        if e.status != 404:
            logger.warning(f"Failed to delete Service {sts_name}: {e}")

    # 3. Delete PVC (StatefulSet 不自动删除 PVC)
    pvc_name = f"workspace-data-{sts_name}-0"
    try:
        core_v1.delete_namespaced_persistent_volume_claim(pvc_name, namespace, body=delete_opts)
        logger.info(f"Deleted PVC: {pvc_name}")
    except ApiException as e:
        if e.status != 404:
            logger.warning(f"Failed to delete PVC {pvc_name}: {e}")

    # 4. Delete ConfigMap
    delete_config_map(f"{sts_name}-config", namespace)


def stream_statefulset_logs(
    sts_name: str,
    namespace: str = "default",
    tail_lines: int = 200,
):
    """
    Generator: yield log lines from StatefulSet pod {sts_name}-0.
    Yields bytes lines. Stops when stream ends or pod not found.
    """
    from kubernetes.client.rest import ApiException

    pod_name = f"{sts_name}-0"
    core_v1 = _get_core_v1_api()
    try:
        resp = core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            follow=True,
            tail_lines=tail_lines,
            _preload_content=False,
        )
        for line in resp:
            yield line
    except ApiException as e:
        error_msg = f"data: [K8s error] {e.status}: {e.reason}\n\n"
        yield error_msg.encode()
    except Exception as e:
        error_msg = f"data: [error] {str(e)}\n\n"
        yield error_msg.encode()

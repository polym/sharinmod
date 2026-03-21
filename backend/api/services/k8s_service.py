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
            ports=[
                client.V1ServicePort(port=80, name="placeholder"),
                client.V1ServicePort(port=8080, name="filebrowser"),
            ],
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
    mount_path = root_cfg.get("workspace_mount_path") or "/app/workspace"
    prunc_enabled = root_cfg.get("prunc_enabled", False) is True  # guard against bool("false") == True
    rootfs_storage_class = root_cfg.get("rootfs_storage_class", "")
    rootfs_storage_size = root_cfg.get("rootfs_storage_size", "10Gi")
    if not mount_path.startswith("/"):
        raise ValueError(f"workspace_mount_path must be an absolute path, got: {mount_path!r}")
    import re as _re
    if not _re.match(r'^[/A-Za-z0-9_\-.]+$', mount_path):
        raise ValueError(f"workspace_mount_path contains invalid characters: {mount_path!r}")
    if prunc_enabled and mount_path == "/.sysdisk":
        raise ValueError(
            "workspace_mount_path cannot be '/.sysdisk' when prunc_enabled=true: "
            "/.sysdisk is reserved for the rootfs PVC mount point"
        )

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
        # claw 容器使用 subPath，只能看到 workspace 子目录
        volume_mounts = [
            client.V1VolumeMount(name="config-volume", mount_path="/config"),
            client.V1VolumeMount(name="workspace-data", mount_path=mount_path, sub_path="workspace"),
        ]
        if prunc_enabled:
            volume_mounts.append(
                client.V1VolumeMount(name="rootfs", mount_path="/.sysdisk")
            )
        container = client.V1Container(
            name="claw",
            image=image,
            image_pull_policy="IfNotPresent",
            command=command,
            volume_mounts=volume_mounts,
        )
        # filebrowser 容器不使用 subPath，看到整个 PVC 根目录
        # .filebrowser.db 在 PVC 根目录，真正的 workspace 在 workspace/ 子目录
        _fb_db = f"{mount_path}/.filebrowser.db"
        _fb_root = f"{mount_path}/workspace"
        _fb_base_url = f"/api/claws/{claw_id}/filebrowser"
        _fb_init = f'''\
mkdir -p "{_fb_root}"
DB_PATH="{_fb_db}"
BASE_URL="{_fb_base_url}"
ROOT_PATH="{_fb_root}"
export FB_NOAUTH=true

# 1. 第一次后台启动 (初始化数据库)
filebrowser -d "$DB_PATH" --address 0.0.0.0 --port 8080 --root "$ROOT_PATH" --noauth --baseurl "$BASE_URL" &
FB_PID=$!
sleep 3
kill $FB_PID
wait $FB_PID 2>/dev/null || true

# 2. 清理数据库锁文件
rm -f "${{DB_PATH}}-journal" "${{DB_PATH}}-wal"

# 3. 设置中文
filebrowser -d "$DB_PATH" config set --locale zh-cn

# 4. 最终持久化启动
exec filebrowser -d "$DB_PATH" --address 0.0.0.0 --port 8080 --root "$ROOT_PATH" --noauth --baseurl "$BASE_URL"
'''
        filebrowser_container = client.V1Container(
            name="filebrowser",
            image="filebrowser/filebrowser:latest",
            image_pull_policy="IfNotPresent",
            command=["sh", "-c"],
            args=[_fb_init],
            ports=[client.V1ContainerPort(container_port=8080, name="filebrowser")],
            volume_mounts=[
                client.V1VolumeMount(name="workspace-data", mount_path=mount_path),
            ],
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
        volume_claim_templates = [pvc_template]
        if prunc_enabled:
            rootfs_pvc_spec = client.V1PersistentVolumeClaimSpec(
                access_modes=["ReadWriteOnce"],
                resources=client.V1ResourceRequirements(requests={"storage": rootfs_storage_size}),
            )
            if rootfs_storage_class:
                rootfs_pvc_spec.storage_class_name = rootfs_storage_class
            volume_claim_templates.append(
                client.V1PersistentVolumeClaim(
                    metadata=client.V1ObjectMeta(name="rootfs"),
                    spec=rootfs_pvc_spec,
                )
            )
        sts_spec = client.V1StatefulSetSpec(
            service_name=sts_name,
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"app": sts_name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": sts_name}),
                spec=client.V1PodSpec(
                    **({"runtime_class_name": "prunc"} if prunc_enabled else {}),
                    containers=[container, filebrowser_container],
                    volumes=[volume_config],
                    restart_policy="Always",
                ),
            ),
            volume_claim_templates=volume_claim_templates,
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
                _get_core_v1_api().delete_namespaced_service(
                    sts_name, namespace,
                    body=client.V1DeleteOptions(propagation_policy="Foreground"),
                )
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

    # 3. Delete PVCs (StatefulSet 不自动删除 PVC)
    for pvc_name in [f"workspace-data-{sts_name}-0", f"rootfs-{sts_name}-0"]:
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
    container: Optional[str] = None,
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
            **({"container": container} if container else {}),
        )
        for line in resp:
            yield line
    except ApiException as e:
        error_msg = f"data: [K8s error] {e.status}: {e.reason}\n\n"
        yield error_msg.encode()
    except Exception as e:
        error_msg = f"data: [error] {str(e)}\n\n"
        yield error_msg.encode()


def restart_statefulset_pod(sts_name: str, namespace: str = "default") -> None:
    """Restart a StatefulSet by deleting its only pod (sts_name-0)."""
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    pod_name = f"{sts_name}-0"
    core_v1 = _get_core_v1_api()

    try:
        core_v1.delete_namespaced_pod(
            name=pod_name,
            namespace=namespace,
            body=client.V1DeleteOptions(),
        )
        logger.info(f"Restarted StatefulSet {sts_name} by deleting pod {pod_name}")
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"Pod {pod_name} not found, StatefulSet may not be running")
        else:
            logger.error(f"Failed to delete pod {pod_name}: {e}")
            raise

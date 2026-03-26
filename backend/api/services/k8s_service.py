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


def _get_custom_objects_api():
    """Load kubeconfig and return CustomObjectsApi client for CRD operations."""
    from kubernetes import client, config

    kubeconfig_path = os.getenv("KUBECONFIG_PATH", os.path.expanduser("~/.kube/config"))
    try:
        config.load_kube_config(config_file=kubeconfig_path)
    except Exception:
        config.load_incluster_config()
    return client.CustomObjectsApi()


def create_pvc(
    name: str,
    storage_size: str,
    storage_class: Optional[str],
    labels: dict,
    namespace: str = "default",
) -> str:
    """
    Create a K8s PVC with the given name, storage size, storage class, and labels.
    Returns the PVC name on success.
    """
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    core_v1 = _get_core_v1_api()
    pvc_spec = client.V1PersistentVolumeClaimSpec(
        access_modes=["ReadWriteOnce"],
        resources=client.V1ResourceRequirements(requests={"storage": storage_size}),
    )
    if storage_class:
        pvc_spec.storage_class_name = storage_class
    pvc = client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(name=name, namespace=namespace, labels=labels),
        spec=pvc_spec,
    )
    core_v1.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc)
    logger.info(f"Created PVC: {name} in namespace {namespace}")
    return name


def delete_pvc(name: str, namespace: str = "default") -> None:
    """
    Delete a K8s PVC by name. Silently ignores 404.
    """
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    core_v1 = _get_core_v1_api()
    try:
        core_v1.delete_namespaced_persistent_volume_claim(
            name=name,
            namespace=namespace,
            body=client.V1DeleteOptions(propagation_policy="Foreground"),
        )
        logger.info(f"Deleted PVC: {name} in namespace {namespace}")
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"PVC {name} not found, skipping deletion")
        else:
            logger.error(f"Failed to delete PVC {name}: {e}")
            raise


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
                client.V1ServicePort(port=3000, name="openclaw-web"),
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
    Create: ConfigMap + PVCs (workspace, optional rootfs) + Headless Service + StatefulSet.
    Returns StatefulSet name on success. Rolls back on failure.
    """
    import time as _time
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
    pvc_created = False
    rootfs_pvc_created = False

    # 生成唯一标识符：timestamp + 4位随机数，避免同一秒内创建相同 claw_id 的竞态条件
    # Fix #6: 防止竞态条件导致的 PVC 名称冲突
    import random as _random
    timestamp = int(_time.time())
    unique_suffix = f"{timestamp}-{_random.randint(1000, 9999)}"

    try:
        # Task 3: 创建 workspace-data PVC
        workspace_pvc_name = f"{sts_name}-workspace-{unique_suffix}"
        workspace_labels = {"app": sts_name, "pvc-type": "workspace"}
        create_pvc(workspace_pvc_name, storage_size, storage_class, workspace_labels, namespace)
        pvc_created = True

        # Task 4: 创建 rootfs PVC（如果 prunc_enabled=true）
        rootfs_pvc_name = None
        if prunc_enabled:
            rootfs_pvc_name = f"{sts_name}-rootfs-{unique_suffix}"
            rootfs_labels = {"app": sts_name, "pvc-type": "rootfs"}
            create_pvc(rootfs_pvc_name, rootfs_storage_size, rootfs_storage_class, rootfs_labels, namespace)
            rootfs_pvc_created = True

        create_headless_service(claw_id, namespace)
        svc_created = True

        volume_config = client.V1Volume(
            name="config-volume",
            config_map=client.V1ConfigMapVolumeSource(name=configmap_name),
        )
        # Task 5: 直接挂载已创建的 PVC
        workspace_volume = client.V1Volume(
            name="workspace-data",
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=workspace_pvc_name),
        )

        # 构建 volumes 列表
        volumes = [volume_config, workspace_volume]
        if prunc_enabled:
            rootfs_volume = client.V1Volume(
                name="rootfs",
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=rootfs_pvc_name),
            )
            volumes.append(rootfs_volume)

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
        _fb_init = (
            f'mkdir -p "{_fb_root}" && '
            f'export FB_DB="{_fb_db}"; '
            f'export FB_NOAUTH=true; '
            f'exec filebrowser -d "$FB_DB" --address 0.0.0.0 --port 8080 --root "{_fb_root}" '
            f'--noauth --baseurl /api/claws/{claw_id}/filebrowser'
        )
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
        sts_spec = client.V1StatefulSetSpec(
            service_name=sts_name,
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"app": sts_name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": sts_name}),
                spec=client.V1PodSpec(
                    **({"runtime_class_name": "prunc"} if prunc_enabled else {}),
                    containers=[container, filebrowser_container],
                    volumes=volumes,
                    restart_policy="Always",
                ),
            ),
            volume_claim_templates=[],  # Task 5: 不再使用 volume_claim_templates
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
        # Task 6: 回滚逻辑 - 清理已创建的资源
        if svc_created:
            try:
                _get_core_v1_api().delete_namespaced_service(
                    sts_name, namespace,
                    body=client.V1DeleteOptions(propagation_policy="Foreground"),
                )
            except Exception as e:
                logger.warning(f"Rollback: failed to delete headless Service {sts_name}: {e}")
        # 清理 PVC（先 rootfs 后 workspace）
        if rootfs_pvc_created:
            try:
                delete_pvc(rootfs_pvc_name, namespace)
            except Exception as e:
                logger.warning(f"Rollback: failed to delete PVC {rootfs_pvc_name}: {e}")
        if pvc_created:
            try:
                delete_pvc(workspace_pvc_name, namespace)
            except Exception as e:
                logger.warning(f"Rollback: failed to delete PVC {workspace_pvc_name}: {e}")
        try:
            delete_config_map(configmap_name, namespace)
        except Exception as e:
            logger.warning(f"Rollback: failed to delete ConfigMap {configmap_name}: {e}")
        raise


def delete_statefulset(sts_name: str, namespace: str = "default") -> None:
    """
    Delete StatefulSet, its headless Service, PVCs, and ConfigMap.

    Ignores 404 for individual resources. Raises on critical failures.

    Fix #7, #8: 改进错误处理，避免 PVC 孤立
    - 如果 StatefulSet 删除失败（非 404），抛出异常，不继续删除 PVC
    - 如果 list PVC 失败（非 404），记录 error 并抛出异常
    """
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    apps_v1 = _get_apps_v1_api()
    core_v1 = _get_core_v1_api()
    delete_opts = client.V1DeleteOptions(propagation_policy="Foreground")

    # 1. Delete StatefulSet
    # Fix #8: 如果 StatefulSet 删除失败，不继续删除 PVC，避免资源不一致
    try:
        apps_v1.delete_namespaced_stateful_set(sts_name, namespace, body=delete_opts)
        logger.info(f"Deleted StatefulSet: {sts_name}")
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"StatefulSet {sts_name} not found, continuing cleanup")
        else:
            logger.error(f"Failed to delete StatefulSet {sts_name}: {e}")
            raise

    # 2. Delete Headless Service
    try:
        core_v1.delete_namespaced_service(sts_name, namespace, body=delete_opts)
        logger.info(f"Deleted headless Service: {sts_name}")
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"Service {sts_name} not found")
        else:
            logger.warning(f"Failed to delete Service {sts_name}: {e}")

    # 3. Delete PVCs using label selector
    # Fix #7: 如果 list PVC 失败（非 404），记录 error 并抛出异常
    pvcs_deleted = 0
    pvc_errors = []
    try:
        pvcs = core_v1.list_namespaced_persistent_volume_claim(
            namespace=namespace,
            label_selector=f"app={sts_name}",
        )
        for pvc in pvcs.items:
            try:
                core_v1.delete_namespaced_persistent_volume_claim(
                    pvc.metadata.name, namespace, body=delete_opts
                )
                logger.info(f"Deleted PVC: {pvc.metadata.name}")
                pvcs_deleted += 1
            except ApiException as e:
                if e.status == 404:
                    logger.warning(f"PVC {pvc.metadata.name} not found")
                else:
                    err_msg = f"Failed to delete PVC {pvc.metadata.name}: {e}"
                    logger.error(err_msg)
                    pvc_errors.append(err_msg)
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"Namespace {namespace} not found when listing PVCs")
        else:
            err_msg = f"Failed to list PVCs for deletion: {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg) from e

    # 如果有 PVC 删除错误，抛出异常通知调用者
    if pvc_errors:
        raise RuntimeError(f"Failed to delete {len(pvc_errors)} PVC(s): {'; '.join(pvc_errors)}")

    if pvcs_deleted > 0:
        logger.info(f"Deleted {pvcs_deleted} PVC(s) for {sts_name}")

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


def get_pod_status(namespace: str, pod_name: str) -> dict:
    """
    返回 Pod 状态，重点关注 claw 容器的状态。

    Args:
        namespace: K8s namespace
        pod_name: Pod name (e.g., claw-123-0)

    Returns:
        dict 包含:
        - phase: Pod Phase (Pending/Running/Failed/Unknown/Succeeded)
        - claw_ready: claw 容器是否 Ready (bool)，None 表示无法确定
        - waiting_reason: claw 容器的等待原因 (str)，None 表示没有等待原因
        - error: 错误信息 (str)，None 表示无错误
    """
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    core_v1 = _get_core_v1_api()
    try:
        pod = core_v1.read_namespaced_pod(pod_name, namespace=namespace)

        phase = pod.status.phase if pod.status else "Unknown"

        # 检查 claw 容器的 ready 和 waiting 状态
        claw_ready = None
        waiting_reason = None

        if pod.status.container_statuses:
            for cs in pod.status.container_statuses:
                if cs.name == "claw":
                    claw_ready = cs.ready
                    # 检查 waiting 状态
                    if cs.state and cs.state.waiting and cs.state.waiting.reason:
                        waiting_reason = cs.state.waiting.reason
                    break

        return {
            "phase": phase,
            "claw_ready": claw_ready,
            "waiting_reason": waiting_reason,
            "error": None,
        }
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"Pod {pod_name} not found in namespace {namespace}")
            return {
                "phase": "NotFound",
                "claw_ready": None,
                "waiting_reason": None,
                "error": "Pod not found",
            }
        else:
            logger.error(f"Error querying pod {pod_name}: {e}")
            return {
                "phase": "Unknown",
                "claw_ready": None,
                "waiting_reason": None,
                "error": str(e),
            }


def exec_pod_command_stream(
    sts_name: str,
    command: list,
    namespace: str = "default",
    container: str = "claw",
    timeout_seconds: int = 600,
):
    """
    Execute a command in a StatefulSet pod and yield stdout/stderr chunks.
    Waits for the pod to be Running before attempting exec.
    Uses kubernetes.stream for WebSocket-based exec.
    """
    from kubernetes.stream import stream as k8s_stream
    from kubernetes.client.rest import ApiException
    import time

    pod_name = f"{sts_name}-0"
    core_v1 = _get_core_v1_api()

    # Wait for pod to be Running before attempting exec
    wait_start = time.time()
    while True:
        if time.time() - wait_start > timeout_seconds:
            yield "[超时：等待龙虾🦞启动超时]\n"
            return
        try:
            pod = core_v1.read_namespaced_pod(pod_name, namespace)
            phase = pod.status.phase if pod.status else None
            if phase == "Running":
                break
            elif phase in ("Failed", "Unknown"):
                yield f"[龙虾🦞状态异常: {phase}，无法执行命令]\n"
                return
            else:
                yield f"[等待龙虾🦞启动 (当前状态: {phase or 'Pending'})...]\n"
        except ApiException as e:
            if e.status == 404:
                yield "[等待龙虾🦞创建...]\n"
            else:
                yield f"[K8s 错误] {e.status}: {e.reason}\n"
                return
        time.sleep(3)

    try:
        exec_stream = k8s_stream(
            core_v1.connect_get_namespaced_pod_exec,
            pod_name,
            namespace,
            command=command,
            container=container,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
            _preload_content=False,
        )
        start = time.time()
        while exec_stream.is_open():
            if time.time() - start > timeout_seconds:
                yield "[超时：二维码获取超时]\n"
                break
            exec_stream.update(timeout=1)
            if exec_stream.peek_stdout():
                yield exec_stream.read_stdout()
            if exec_stream.peek_stderr():
                yield exec_stream.read_stderr()
    except ApiException as e:
        yield f"[K8s 错误] {e.status}: {e.reason}\n"
    except Exception as e:
        yield f"[错误] {str(e)}\n"


def create_snapshot(
    claw_id: int,
    pvc_name: str,
    pvc_type: str,
    timestamp: str,
    namespace: str = "default",
) -> str:
    """
    Create a VolumeSnapshot for a PVC using CustomObjectsApi.

    Args:
        claw_id: ID of the claw
        pvc_name: Name of the PVC to snapshot
        pvc_type: Type of PVC (workspace-data or rootfs)
        timestamp: Timestamp for snapshot versioning
        namespace: K8s namespace

    Returns:
        Snapshot name
    """
    from kubernetes.client.rest import ApiException

    custom_api = _get_custom_objects_api()
    core_v1 = _get_core_v1_api()

    # Get the PVC to get its storage class
    try:
        pvc = core_v1.read_namespaced_persistent_volume_claim(pvc_name, namespace)
        storage_class = pvc.spec.storage_class_name
    except ApiException as e:
        if e.status == 404:
            logger.error(f"PVC {pvc_name} not found")
            raise
        raise

    snapshot_name = f"claw-{claw_id}-{pvc_type}-{timestamp}"

    # VolumeSnapshot CRD structure
    snapshot = {
        "apiVersion": "snapshot.storage.k8s.io/v1",
        "kind": "VolumeSnapshot",
        "metadata": {
            "name": snapshot_name,
            "namespace": namespace,
            "labels": {
                "app": f"claw-{claw_id}",
                "archive-timestamp": timestamp,
                "pvc-type": pvc_type,
                "archive-auto-created": "false",  # Manual archive
            },
        },
        "spec": {
            "source": {
                "persistentVolumeClaimName": pvc_name,
            },
            "volumeSnapshotClassName": "topolvm-snapclass",
        },
    }

    group = "snapshot.storage.k8s.io"
    version = "v1"
    plural = "volumesnapshots"

    try:
        custom_api.create_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            body=snapshot,
        )
        logger.info(f"Created VolumeSnapshot: {snapshot_name}")
        return snapshot_name
    except ApiException as e:
        logger.error(f"Failed to create VolumeSnapshot {snapshot_name}: {e}")
        raise


def list_snapshots(claw_id: int, namespace: str = "default") -> list:
    """
    List all VolumeSnapshots for a claw, grouped by timestamp.

    Args:
        claw_id: ID of the claw
        namespace: K8s namespace

    Returns:
        List of archive items, each containing timestamp, workspace_snapshot_name,
        rootfs_snapshot_name, and created_at
    """
    from kubernetes.client.rest import ApiException
    from collections import defaultdict

    custom_api = _get_custom_objects_api()

    group = "snapshot.storage.k8s.io"
    version = "v1"
    plural = "volumesnapshots"

    try:
        snapshots = custom_api.list_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            label_selector=f"app=claw-{claw_id}",
        )
    except ApiException as e:
        if e.status == 404:
            return []
        logger.error(f"Failed to list snapshots for claw-{claw_id}: {e}")
        raise

    # Group snapshots by timestamp
    archive_groups = defaultdict(lambda: {"workspace": None, "rootfs": None, "created_at": None, "ready_to_use": None, "auto_created": False})

    for snap in snapshots.get("items", []):
        labels = snap.get("metadata", {}).get("labels", {})
        timestamp = labels.get("archive-timestamp")
        pvc_type = labels.get("pvc-type")
        created_at = snap.get("metadata", {}).get("creationTimestamp")
        # Check if snapshot is ready to use
        ready_to_use = snap.get("status", {}).get("readyToUse", False)
        # Check if archive is auto-created
        auto_created = labels.get("archive-auto-created", "false").lower() == "true"

        if timestamp and pvc_type:
            # Map pvc_type to archive type key
            # "workspace-data" -> "workspace", "rootfs" -> "rootfs"
            archive_type = "workspace" if pvc_type == "workspace-data" else pvc_type
            archive_groups[timestamp][archive_type] = snap.get("metadata", {}).get("name")
            if created_at:
                archive_groups[timestamp]["created_at"] = created_at
            # Archive is ready only if all snapshots are ready
            if archive_groups[timestamp]["ready_to_use"] is None:
                archive_groups[timestamp]["ready_to_use"] = ready_to_use
            else:
                archive_groups[timestamp]["ready_to_use"] = archive_groups[timestamp]["ready_to_use"] and ready_to_use
            # Set auto_created flag (compatibility: old archives without label are manual)
            archive_groups[timestamp]["auto_created"] = auto_created

    # Convert to list and sort by timestamp descending
    # Only include archives that have at least a workspace snapshot
    result = [
        {
            "timestamp": ts,
            "workspace_snapshot_name": data["workspace"],
            "rootfs_snapshot_name": data["rootfs"],
            "created_at": data["created_at"],
            "ready_to_use": data.get("ready_to_use", False),
            "auto_created": data.get("auto_created", False),
        }
        for ts, data in sorted(archive_groups.items(), key=lambda x: x[0], reverse=True)
        if data["workspace"]  # Must have workspace snapshot
    ]

    return result


def restore_from_snapshot(
    claw_id: int,
    timestamp: str,
    workspace_snapshot_name: str,
    rootfs_snapshot_name: Optional[str],
    namespace: str = "default",
) -> None:
    """
    Restore a claw from snapshots by creating new PVCs and updating StatefulSet.

    Args:
        claw_id: ID of the claw
        timestamp: Archive timestamp
        workspace_snapshot_name: Name of workspace snapshot
        rootfs_snapshot_name: Name of rootfs snapshot (optional)
        namespace: K8s namespace

    The process:
    1. Stop StatefulSet (set replicas to 0)
    2. Wait for pods to terminate
    3. Create new PVCs from snapshots
    4. Update StatefulSet volume references to new PVCs
    5. Start StatefulSet (set replicas back to 1)
    6. Delete old PVCs
    """
    import time
    import random
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    core_v1 = _get_core_v1_api()
    apps_v1 = _get_apps_v1_api()

    sts_name = f"claw-{claw_id}"

    # Generate unique suffix for new PVCs
    unique_suffix = f"{int(time.time())}-{random.randint(1000, 9999)}"

    # Get current PVC info from StatefulSet to find storage class and size
    def _get_current_pvc_info(pvc_type: str) -> tuple:
        """Get storage class and size from current PVC used by StatefulSet."""
        pvcs = core_v1.list_namespaced_persistent_volume_claim(
            namespace=namespace,
            label_selector=f"app={sts_name},pvc-type={pvc_type}",
        )
        if not pvcs.items:
            raise ValueError(f"No current PVC found for {pvc_type}")
        pvc = pvcs.items[0]
        storage_class = pvc.spec.storage_class_name
        storage_size = pvc.spec.resources.requests["storage"]
        return storage_class, storage_size

    # Step 1: Stop StatefulSet (set replicas to 0)
    try:
        sts = apps_v1.read_namespaced_stateful_set(sts_name, namespace)
        sts.spec.replicas = 0
        apps_v1.patch_namespaced_stateful_set(
            name=sts_name,
            namespace=namespace,
            body=sts,
        )
        logger.info(f"Stopped StatefulSet {sts_name} by setting replicas to 0")
    except ApiException as e:
        logger.error(f"Failed to stop StatefulSet {sts_name}: {e}")
        raise

    # Step 2: Create new PVCs from snapshots
    ws_storage_class, ws_storage_size = _get_current_pvc_info("workspace")
    new_workspace_pvc = f"{sts_name}-workspace-{unique_suffix}"
    new_workspace_labels = {"app": sts_name, "pvc-type": "workspace"}

    create_pvc_from_snapshot(
        new_workspace_pvc,
        workspace_snapshot_name,
        ws_storage_size,
        ws_storage_class,
        new_workspace_labels,
        namespace,
    )

    # Create new rootfs PVC from snapshot (if exists)
    new_rootfs_pvc = None
    if rootfs_snapshot_name:
        rootfs_storage_class, rootfs_storage_size = _get_current_pvc_info("rootfs")
        new_rootfs_pvc = f"{sts_name}-rootfs-{unique_suffix}"
        new_rootfs_labels = {"app": sts_name, "pvc-type": "rootfs"}

        create_pvc_from_snapshot(
            new_rootfs_pvc,
            rootfs_snapshot_name,
            rootfs_storage_size,
            rootfs_storage_class,
            new_rootfs_labels,
            namespace,
        )

    # Step 4: Update StatefulSet to use new PVCs
    try:
        sts = apps_v1.read_namespaced_stateful_set(sts_name, namespace)

        # Find and update volume references
        pod_spec = sts.spec.template.spec
        for volume in pod_spec.volumes:
            if volume.name == "workspace-data" and volume.persistent_volume_claim:
                volume.persistent_volume_claim.claim_name = new_workspace_pvc
            elif volume.name == "rootfs" and volume.persistent_volume_claim and new_rootfs_pvc:
                volume.persistent_volume_claim.claim_name = new_rootfs_pvc

        # Step 5: Start StatefulSet (set replicas to 1)
        sts.spec.replicas = 1
        apps_v1.patch_namespaced_stateful_set(
            name=sts_name,
            namespace=namespace,
            body=sts,
        )
        logger.info(f"Updated StatefulSet {sts_name} to use new PVCs and set replicas to 1")

    except ApiException as e:
        logger.error(f"Failed to update StatefulSet {sts_name}: {e}")
        raise

    # Step 6: Delete old PVCs using label selector (excluding new ones)
    try:
        old_pvcs = core_v1.list_namespaced_persistent_volume_claim(
            namespace=namespace,
            label_selector=f"app={sts_name}",
        )
        for pvc in old_pvcs.items:
            if pvc.metadata.name not in [new_workspace_pvc, new_rootfs_pvc]:
                try:
                    core_v1.delete_namespaced_persistent_volume_claim(
                        name=pvc.metadata.name,
                        namespace=namespace,
                        body=client.V1DeleteOptions(propagation_policy="Foreground"),
                    )
                    logger.info(f"Deleted old PVC: {pvc.metadata.name}")
                except ApiException as e:
                    if e.status == 404:
                        logger.warning(f"PVC {pvc.metadata.name} not found")
                    else:
                        logger.warning(f"Failed to delete old PVC {pvc.metadata.name}: {e}")
    except ApiException as e:
        logger.warning(f"Failed to list old PVCs for deletion: {e}")

    logger.info(f"Successfully restored claw-{claw_id} to archive {timestamp}")


def create_pvc_from_snapshot(
    name: str,
    snapshot_name: str,
    storage_size: str,
    storage_class: Optional[str],
    labels: dict,
    namespace: str = "default",
) -> str:
    """
    Create a PVC from a VolumeSnapshot.

    Args:
        name: Name for the new PVC
        snapshot_name: Name of the VolumeSnapshot to restore from
        storage_size: Storage size for the PVC
        storage_class: StorageClass for the PVC
        labels: Labels to apply to the PVC
        namespace: K8s namespace

    Returns:
        PVC name
    """
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    core_v1 = _get_core_v1_api()

    # Build PVC spec with dataSource as dict
    pvc_dict = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": labels,
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {
                "requests": {
                    "storage": storage_size,
                },
            },
            "dataSource": {
                "kind": "VolumeSnapshot",
                "apiGroup": "snapshot.storage.k8s.io",
                "name": snapshot_name,
            },
        },
    }

    if storage_class:
        pvc_dict["spec"]["storageClassName"] = storage_class

    # Use create_namespaced_persistent_volume_claim with dict body
    core_v1.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc_dict)
    logger.info(f"Created PVC from snapshot: {name}")
    return name


def delete_snapshot(
    claw_id: int,
    timestamp: str,
    namespace: str = "default",
) -> None:
    """
    Delete a VolumeSnapshot for a claw by timestamp.

    Args:
        claw_id: ID of the claw
        timestamp: Archive timestamp
        namespace: K8s namespace

    Deletes both workspace and rootfs snapshots with the given timestamp.
    """
    from kubernetes.client.rest import ApiException

    custom_api = _get_custom_objects_api()
    group = "snapshot.storage.k8s.io"
    version = "v1"
    plural = "volumesnapshots"

    # Delete workspace snapshot
    workspace_snapshot_name = f"claw-{claw_id}-workspace-data-{timestamp}"
    try:
        custom_api.delete_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=workspace_snapshot_name,
        )
        logger.info(f"Deleted VolumeSnapshot: {workspace_snapshot_name}")
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"VolumeSnapshot {workspace_snapshot_name} not found")
        else:
            logger.error(f"Failed to delete VolumeSnapshot {workspace_snapshot_name}: {e}")
            raise

    # Delete rootfs snapshot
    rootfs_snapshot_name = f"claw-{claw_id}-rootfs-{timestamp}"
    try:
        custom_api.delete_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=rootfs_snapshot_name,
        )
        logger.info(f"Deleted VolumeSnapshot: {rootfs_snapshot_name}")
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"VolumeSnapshot {rootfs_snapshot_name} not found")
        else:
            logger.error(f"Failed to delete VolumeSnapshot {rootfs_snapshot_name}: {e}")
            raise


def cleanup_old_archives(
    claw_id: int,
    namespace: str = "default",
    retention_config: dict = None,
) -> None:
    """
    Clean up old archives based on retention policy.

    Args:
        claw_id: ID of the claw
        namespace: K8s namespace
        retention_config: Retention policy config with keys:
            - daily_retention: Number of daily backups to keep (default: 1)
            - interval_retention: Number of interval backups to keep (default: 5)
    """
    from kubernetes.client.rest import ApiException

    if retention_config is None:
        retention_config = {
            "daily_retention": 1,
            "interval_retention": 5,
        }

    custom_api = _get_custom_objects_api()
    group = "snapshot.storage.k8s.io"
    version = "v1"
    plural = "volumesnapshots"

    try:
        snapshots = custom_api.list_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            label_selector=f"app=claw-{claw_id}",
        )
    except ApiException as e:
        logger.error(f"Failed to list snapshots for cleanup: {e}")
        return

    # Group snapshots by auto_created and auto_schedule labels
    daily_archives = []  # archive-auto-schedule=daily
    interval_archives = []  # archive-auto-schedule=interval
    manual_archives = []  # archive-auto-created=false or missing

    for snap in snapshots.get("items", []):
        labels = snap.get("metadata", {}).get("labels", {})
        auto_created = labels.get("archive-auto-created", "false").lower() == "true"
        auto_schedule = labels.get("archive-auto-schedule")
        timestamp = labels.get("archive-timestamp")

        if not timestamp:
            continue

        snap_info = {
            "name": snap.get("metadata", {}).get("name"),
            "timestamp": timestamp,
            "creationTimestamp": snap.get("metadata", {}).get("creationTimestamp"),
        }

        if auto_created and auto_schedule == "daily":
            daily_archives.append(snap_info)
        elif auto_created and auto_schedule == "interval":
            interval_archives.append(snap_info)
        elif not auto_created:
            manual_archives.append(snap_info)

    # Sort by creation time (newest first)
    daily_archives.sort(key=lambda x: x["creationTimestamp"], reverse=True)
    interval_archives.sort(key=lambda x: x["creationTimestamp"], reverse=True)

    # Clean up old daily archives (keep only retention count)
    daily_retention = retention_config.get("daily_retention", 1)
    for archive in daily_archives[daily_retention:]:
        try:
            custom_api.delete_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=archive["name"],
            )
            logger.info(f"Cleaned up old daily archive: {archive['name']}")
        except ApiException as e:
            if e.status != 404:
                logger.warning(f"Failed to cleanup old archive {archive['name']}: {e}")

    # Clean up old interval archives (keep only retention count)
    interval_retention = retention_config.get("interval_retention", 5)
    for archive in interval_archives[interval_retention:]:
        try:
            custom_api.delete_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=archive["name"],
            )
            logger.info(f"Cleaned up old interval archive: {archive['name']}")
        except ApiException as e:
            if e.status != 404:
                logger.warning(f"Failed to cleanup old archive {archive['name']}: {e}")

def create_auto_archive(
    claw_id: int,
    namespace: str = "default",
    schedule_type: str = "interval",
) -> str | None:
    """
    Create an automatic archive for a claw.

    Args:
        claw_id: ID of the claw
        namespace: K8s namespace
        schedule_type: Type of schedule ('daily' or 'interval')

    Returns:
        Timestamp of created archive, or None if failed

    Creates workspace and rootfs snapshots with auto-created labels.
    """
    import time
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    logger.info(f"[AutoArchive] Creating {schedule_type} archive for claw-{claw_id} (namespace: {namespace})")
    core_v1 = _get_core_v1_api()
    timestamp = str(int(time.time()))

    try:
        # Get current PVCs
        logger.debug(f"[AutoArchive] claw-{claw_id}: Listing PVCs with label selector: app=claw-{claw_id}")
        pvcs = core_v1.list_namespaced_persistent_volume_claim(
            namespace=namespace,
            label_selector=f"app=claw-{claw_id}",
        )
        logger.debug(f"[AutoArchive] claw-{claw_id}: Found {len(pvcs.items)} PVC(s)")
    except ApiException as e:
        logger.error(f"[AutoArchive] claw-{claw_id}: Failed to list PVCs - {e}")
        return None

    workspace_pvc = None
    rootfs_pvc = None

    for pvc in pvcs.items:
        pvc_type = pvc.metadata.labels.get("pvc-type")
        pvc_name = pvc.metadata.name
        logger.debug(f"[AutoArchive] claw-{claw_id}: Found PVC {pvc_name} (type: {pvc_type})")
        if pvc_type == "workspace":
            workspace_pvc = pvc.metadata.name
        elif pvc_type == "rootfs":
            rootfs_pvc = pvc.metadata.name

    logger.info(f"[AutoArchive] claw-{claw_id}: workspace_pvc={workspace_pvc}, rootfs_pvc={rootfs_pvc}")

    if not workspace_pvc:
        logger.error(f"[AutoArchive] claw-{claw_id}: Workspace PVC not found!")
        return None

    # Create workspace snapshot with auto-created labels
    from kubernetes import client as k8s_client

    custom_api = _get_custom_objects_api()

    # Get storage class
    try:
        pvc = core_v1.read_namespaced_persistent_volume_claim(workspace_pvc, namespace)
        storage_class = pvc.spec.storage_class_name
    except ApiException as e:
        logger.error(f"Failed to read PVC {workspace_pvc}: {e}")
        return None

    snapshot_name = f"claw-{claw_id}-workspace-data-{timestamp}"

    snapshot = {
        "apiVersion": "snapshot.storage.k8s.io/v1",
        "kind": "VolumeSnapshot",
        "metadata": {
            "name": snapshot_name,
            "namespace": namespace,
            "labels": {
                "app": f"claw-{claw_id}",
                "archive-timestamp": timestamp,
                "pvc-type": "workspace-data",
                "archive-auto-created": "true",
                "archive-auto-schedule": schedule_type,
            },
        },
        "spec": {
            "source": {
                "persistentVolumeClaimName": workspace_pvc,
            },
            "volumeSnapshotClassName": "topolvm-snapclass",
        },
    }

    group = "snapshot.storage.k8s.io"
    version = "v1"
    plural = "volumesnapshots"

    try:
        custom_api.create_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            body=snapshot,
        )
        logger.info(f"[AutoArchive] claw-{claw_id}: Created workspace VolumeSnapshot: {snapshot_name} (timestamp: {timestamp})")
    except ApiException as e:
        logger.error(f"[AutoArchive] claw-{claw_id}: Failed to create workspace snapshot {snapshot_name} - {e}")
        return None

    # Create rootfs snapshot if exists
    if rootfs_pvc:
        try:
            pvc = core_v1.read_namespaced_persistent_volume_claim(rootfs_pvc, namespace)
            storage_class = pvc.spec.storage_class_name
        except ApiException as e:
            logger.error(f"Failed to read PVC {rootfs_pvc}: {e}")
            return timestamp  # Return timestamp even if rootfs fails

        rootfs_snapshot_name = f"claw-{claw_id}-rootfs-{timestamp}"

        snapshot = {
            "apiVersion": "snapshot.storage.k8s.io/v1",
            "kind": "VolumeSnapshot",
            "metadata": {
                "name": rootfs_snapshot_name,
                "namespace": namespace,
                "labels": {
                    "app": f"claw-{claw_id}",
                    "archive-timestamp": timestamp,
                    "pvc-type": "rootfs",
                    "archive-auto-created": "true",
                    "archive-auto-schedule": schedule_type,
                },
            },
            "spec": {
                "source": {
                    "persistentVolumeClaimName": rootfs_pvc,
                },
                "volumeSnapshotClassName": "topolvm-snapclass",
            },
        }

        try:
            custom_api.create_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                body=snapshot,
            )
            logger.info(f"[AutoArchive] claw-{claw_id}: Created rootfs VolumeSnapshot: {rootfs_snapshot_name}")
        except ApiException as e:
            logger.error(f"[AutoArchive] claw-{claw_id}: Failed to create rootfs snapshot {rootfs_snapshot_name} - {e}")

    logger.info(f"[AutoArchive] claw-{claw_id}: Auto archive completed successfully (timestamp: {timestamp})")
    return timestamp


def count_manual_archives(claw_id: int, namespace: str = "default") -> int:
    """
    Count the number of manual archives for a claw.

    Args:
        claw_id: ID of the claw
        namespace: K8s namespace

    Returns:
        Number of manual archives (auto_created=false or missing label)
    """
    from kubernetes.client.rest import ApiException

    custom_api = _get_custom_objects_api()
    group = "snapshot.storage.k8s.io"
    version = "v1"
    plural = "volumesnapshots"

    try:
        snapshots = custom_api.list_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            label_selector=f"app=claw-{claw_id}",
        )
    except ApiException as e:
        logger.error(f"Failed to list snapshots for claw-{claw_id}: {e}")
        return 0

    # Count unique manual archive timestamps
    manual_timestamps = set()
    for snap in snapshots.get("items", []):
        labels = snap.get("metadata", {}).get("labels", {})
        auto_created = labels.get("archive-auto-created", "false").lower() == "true"
        timestamp = labels.get("archive-timestamp")

        if timestamp and not auto_created:
            manual_timestamps.add(timestamp)

    return len(manual_timestamps)

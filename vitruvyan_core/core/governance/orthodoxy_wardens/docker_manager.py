"""
Docker Manager - Container Health and Management 
Pure docker-py implementation - NO CrewAI conflicts
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

class DockerManager:
    """
    Docker container management for Vitruvyan services
    Handles health checks, restarts, and resource monitoring
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._initialize_client()
        
        # Track restart history to prevent restart loops
        self.restart_history = {}  # {container_name: [timestamps]}
        self.min_restart_interval = 300  # 5 minutes minimum between restarts
        
        # Vitruvyan container names
        self.vitruvyan_containers = [
            "vitruvyan_api_graph",
            "vitruvyan_api_semantic",
            "vitruvyan_api_neural", 
            "vitruvyan_sentiment_enhanced",  # Updated: Enhanced sentiment service
            "vitruvyan_api_crewai",
            "vitruvyan_api_audit",  # This container
            "vitruvyan_gemma_cognitive",  # NEW: Gemma Cognitive Layer
            "vitruvyan_vault_keepers",  # Backup system (Vault Keepers)
            "vitruvyan_portfolio_guardian",  # NEW: Portfolio guardian
            "vitruvyan_redis",
            "vitruvyan_qdrant"
        ]
    
    def _initialize_client(self):
        """Initialize Docker client"""
        try:
            import docker
            self.client = docker.from_env()
            self.logger.info("Docker client initialized successfully")
            
        except ImportError:
            self.logger.error("docker package not available")
            self.client = None
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
    
    async def check_all_containers(self) -> Dict:
        """
        Check health status of all Vitruvyan containers
        """
        if not self.client:
            return {"error": "Docker client not available"}
        
        try:
            containers_status = {}
            unhealthy = []
            healthy = []
            missing = []
            
            for container_name in self.vitruvyan_containers:
                try:
                    container = self.client.containers.get(container_name)
                    
                    # Get container status
                    status = container.status
                    # Consider starting/restarting containers as transitional, not unhealthy
                    health = "healthy" if status in ["running", "starting", "restarting"] else "unhealthy"
                    
                    # Get additional info
                    container_info = {
                        "status": status,
                        "health": health,
                        "image": container.image.tags[0] if container.image.tags else "unknown",
                        "created": container.attrs.get("Created", "unknown"),
                        "ports": self._extract_ports(container),
                        "restart_count": container.attrs.get("RestartCount", 0)
                    }
                    
                    # Get resource usage if running
                    if status == "running":
                        try:
                            stats = container.stats(stream=False)
                            container_info["resources"] = self._parse_container_stats(stats)
                        except Exception as stats_error:
                            self.logger.warning(f"Could not get stats for {container_name}: {stats_error}")
                    
                    containers_status[container_name] = container_info
                    
                    if health == "healthy":
                        healthy.append(container_name)
                    else:
                        unhealthy.append(container_name) 
                        
                except Exception as e:
                    if "No such container" in str(e):
                        missing.append(container_name)
                        containers_status[container_name] = {
                            "status": "missing",
                            "health": "missing",
                            "error": "Container not found"
                        }
                    else:
                        self.logger.error(f"Error checking container {container_name}: {e}")
                        containers_status[container_name] = {
                            "status": "error",
                            "health": "error", 
                            "error": str(e)
                        }
                        unhealthy.append(container_name)
            
            return {
                "containers": containers_status,
                "summary": {
                    "total": len(self.vitruvyan_containers),
                    "healthy": len(healthy),
                    "unhealthy": len(unhealthy),
                    "missing": len(missing),
                    "health_percentage": (len(healthy) / len(self.vitruvyan_containers)) * 100
                },
                "healthy": healthy,
                "unhealthy": unhealthy,
                "missing": missing,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Container health check failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def restart_container(self, container_name: str) -> Dict:
        """
        Restart a specific container with restart loop prevention
        """
        if not self.client:
            return {"error": "Docker client not available"}
        
        # Check restart history to prevent loops
        now = datetime.now()
        if container_name in self.restart_history:
            # Keep only recent restarts (last hour)
            self.restart_history[container_name] = [
                ts for ts in self.restart_history[container_name] 
                if (now - ts).total_seconds() < 3600
            ]
            
            # Check if too many recent restarts
            if len(self.restart_history[container_name]) >= 3:
                self.logger.warning(f"Too many recent restarts for {container_name}, skipping")
                return {
                    "action": "restart",
                    "container": container_name,
                    "status": "skipped",
                    "reason": "too_many_restarts",
                    "timestamp": now.isoformat()
                }
            
            # Check minimum interval
            if self.restart_history[container_name]:
                last_restart = self.restart_history[container_name][-1]
                if (now - last_restart).total_seconds() < self.min_restart_interval:
                    self.logger.warning(f"Restart too soon for {container_name}, waiting")
                    return {
                        "action": "restart",
                        "container": container_name,
                        "status": "skipped", 
                        "reason": "minimum_interval_not_met",
                        "timestamp": now.isoformat()
                    }
        else:
            self.restart_history[container_name] = []
        
        try:
            container = self.client.containers.get(container_name)
            
            self.logger.info(f"Restarting container: {container_name}")
            
            # Record restart attempt
            self.restart_history[container_name].append(now)
            
            # Record pre-restart status
            pre_status = container.status
            
            # Restart the container
            container.restart(timeout=30)
            
            # Wait a moment for restart
            await asyncio.sleep(3)
            
            # Check post-restart status
            container.reload()
            post_status = container.status
            
            success = post_status == "running"
            
            result = {
                "action": "restart",
                "container": container_name,
                "status": "success" if success else "failed",
                "pre_restart_status": pre_status,
                "post_restart_status": post_status,
                "timestamp": datetime.now().isoformat()
            }
            
            if success:
                self.logger.info(f"Container {container_name} restarted successfully")
            else:
                self.logger.error(f"Container {container_name} restart failed - status: {post_status}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to restart container {container_name}: {e}")
            return {
                "action": "restart",
                "container": container_name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def stop_container(self, container_name: str) -> Dict:
        """
        Stop a specific container
        """
        if not self.client:
            return {"error": "Docker client not available"}
        
        try:
            container = self.client.containers.get(container_name)
            
            self.logger.info(f"Stopping container: {container_name}")
            
            container.stop(timeout=10)
            
            return {
                "action": "stop",
                "container": container_name,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to stop container {container_name}: {e}")
            return {
                "action": "stop",
                "container": container_name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_container(self, container_name: str) -> Dict:
        """
        Start a specific container
        """
        if not self.client:
            return {"error": "Docker client not available"}
        
        try:
            container = self.client.containers.get(container_name)
            
            self.logger.info(f"Starting container: {container_name}")
            
            container.start()
            
            # Wait for startup
            await asyncio.sleep(2)
            container.reload()
            
            return {
                "action": "start",
                "container": container_name, 
                "status": "success" if container.status == "running" else "failed",
                "current_status": container.status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start container {container_name}: {e}")
            return {
                "action": "start",
                "container": container_name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_container_logs(self, container_name: str, lines: int = 50) -> Dict:
        """
        Get recent logs from a container
        """
        if not self.client:
            return {"error": "Docker client not available"}
        
        try:
            container = self.client.containers.get(container_name)
            
            logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
            
            return {
                "container": container_name,
                "logs": logs,
                "lines_requested": lines,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get logs for {container_name}: {e}")
            return {
                "container": container_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_container_resources(self, container_name: str) -> Dict:
        """
        Get detailed resource usage for a container
        """
        if not self.client:
            return {"error": "Docker client not available"}
        
        try:
            container = self.client.containers.get(container_name)
            
            if container.status != "running":
                return {
                    "container": container_name,
                    "status": container.status,
                    "message": "Container not running"
                }
            
            # Get container stats
            stats = container.stats(stream=False)
            parsed_stats = self._parse_container_stats(stats)
            
            return {
                "container": container_name,
                "resources": parsed_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get resources for {container_name}: {e}")
            return {
                "container": container_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _parse_container_stats(self, stats: Dict) -> Dict:
        """
        Parse Docker container stats into readable format
        """
        try:
            parsed = {}
            
            # CPU usage
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            
            if cpu_stats and precpu_stats:
                cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - \
                           precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                system_delta = cpu_stats.get("system_cpu_usage", 0) - \
                              precpu_stats.get("system_cpu_usage", 0)
                
                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * 100
                    parsed["cpu_percent"] = round(cpu_percent, 2)
            
            # Memory usage
            memory_stats = stats.get("memory_stats", {})
            if memory_stats:
                memory_usage = memory_stats.get("usage", 0)
                memory_limit = memory_stats.get("limit", 0)
                
                parsed["memory_usage_bytes"] = memory_usage
                parsed["memory_limit_bytes"] = memory_limit
                
                if memory_limit > 0:
                    memory_percent = (memory_usage / memory_limit) * 100
                    parsed["memory_percent"] = round(memory_percent, 2)
                
                parsed["memory_usage_mb"] = round(memory_usage / (1024 * 1024), 2)
                parsed["memory_limit_mb"] = round(memory_limit / (1024 * 1024), 2)
            
            # Network I/O
            networks = stats.get("networks", {})
            if networks:
                total_rx_bytes = 0
                total_tx_bytes = 0
                
                for interface, net_data in networks.items():
                    total_rx_bytes += net_data.get("rx_bytes", 0)
                    total_tx_bytes += net_data.get("tx_bytes", 0)
                
                parsed["network_rx_bytes"] = total_rx_bytes  
                parsed["network_tx_bytes"] = total_tx_bytes
                parsed["network_rx_mb"] = round(total_rx_bytes / (1024 * 1024), 2)
                parsed["network_tx_mb"] = round(total_tx_bytes / (1024 * 1024), 2)
            
            # Block I/O
            blkio_stats = stats.get("blkio_stats", {})
            if blkio_stats:
                io_service_bytes = blkio_stats.get("io_service_bytes_recursive", [])
                
                read_bytes = 0
                write_bytes = 0
                
                for io_stat in io_service_bytes:
                    if io_stat.get("op") == "read":
                        read_bytes += io_stat.get("value", 0)
                    elif io_stat.get("op") == "write":
                        write_bytes += io_stat.get("value", 0)
                
                parsed["disk_read_bytes"] = read_bytes
                parsed["disk_write_bytes"] = write_bytes  
                parsed["disk_read_mb"] = round(read_bytes / (1024 * 1024), 2)
                parsed["disk_write_mb"] = round(write_bytes / (1024 * 1024), 2)
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"Failed to parse container stats: {e}")
            return {"parse_error": str(e)}
    
    def _extract_ports(self, container) -> Dict:
        """Extract port mappings from container"""
        try:
            ports = {}
            port_data = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            
            for container_port, host_data in port_data.items():
                if host_data:
                    host_port = host_data[0].get("HostPort")
                    ports[container_port] = host_port
                else:
                    ports[container_port] = None
            
            return ports
            
        except Exception as e:
            self.logger.error(f"Failed to extract ports: {e}")
            return {}
    
    async def cleanup_unused_resources(self) -> Dict:
        """
        Clean up unused Docker resources
        """
        if not self.client:
            return {"error": "Docker client not available"}
        
        cleanup_results = {}
        
        try:
            # Clean up unused containers
            try:
                pruned_containers = self.client.containers.prune()
                cleanup_results["containers"] = {
                    "pruned_count": len(pruned_containers.get("ContainersDeleted", [])),
                    "space_reclaimed": pruned_containers.get("SpaceReclaimed", 0)
                }
            except Exception as e:
                cleanup_results["containers"] = {"error": str(e)}
            
            # Clean up unused images
            try:
                pruned_images = self.client.images.prune()
                cleanup_results["images"] = {
                    "pruned_count": len(pruned_images.get("ImagesDeleted", [])),
                    "space_reclaimed": pruned_images.get("SpaceReclaimed", 0)
                }
            except Exception as e:
                cleanup_results["images"] = {"error": str(e)}
            
            # Clean up unused volumes
            try:
                pruned_volumes = self.client.volumes.prune()
                cleanup_results["volumes"] = {
                    "pruned_count": len(pruned_volumes.get("VolumesDeleted", [])),
                    "space_reclaimed": pruned_volumes.get("SpaceReclaimed", 0)
                }
            except Exception as e:
                cleanup_results["volumes"] = {"error": str(e)}
            
            # Clean up unused networks
            try:
                pruned_networks = self.client.networks.prune()
                cleanup_results["networks"] = {
                    "pruned_count": len(pruned_networks.get("NetworksDeleted", [])),
                    "space_reclaimed": 0  # Networks don't report space
                }
            except Exception as e:
                cleanup_results["networks"] = {"error": str(e)}
            
            # Calculate total space reclaimed
            total_space = 0
            for resource, data in cleanup_results.items():
                if isinstance(data, dict) and "space_reclaimed" in data:
                    total_space += data["space_reclaimed"]
            
            return {
                "action": "docker_cleanup",
                "status": "completed",
                "cleanup_results": cleanup_results,
                "total_space_reclaimed_bytes": total_space,
                "total_space_reclaimed_mb": round(total_space / (1024 * 1024), 2),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Docker cleanup failed: {e}")
            return {
                "action": "docker_cleanup",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def monitor_container_health(self, container_name: str, duration_minutes: int = 5) -> Dict:
        """
        Monitor a container's health over time
        """
        if not self.client:
            return {"error": "Docker client not available"}
        
        measurements = []
        interval = 30  # 30 seconds between measurements
        num_measurements = (duration_minutes * 60) // interval
        
        try:
            container = self.client.containers.get(container_name)
            
            if container.status != "running":
                return {
                    "container": container_name,
                    "error": f"Container not running (status: {container.status})"
                }
            
            for i in range(num_measurements):
                try:
                    # Get current stats
                    stats = container.stats(stream=False)
                    parsed_stats = self._parse_container_stats(stats)
                    
                    measurement = {
                        "timestamp": datetime.now().isoformat(),
                        "cpu_percent": parsed_stats.get("cpu_percent", 0),
                        "memory_percent": parsed_stats.get("memory_percent", 0),
                        "memory_usage_mb": parsed_stats.get("memory_usage_mb", 0),
                        "network_rx_mb": parsed_stats.get("network_rx_mb", 0),
                        "network_tx_mb": parsed_stats.get("network_tx_mb", 0)
                    }
                    measurements.append(measurement)
                    
                    # Refresh container object
                    container.reload()
                    if container.status != "running":
                        break
                    
                    if i < num_measurements - 1:  # Don't sleep after last measurement
                        await asyncio.sleep(interval)
                        
                except Exception as measurement_error:
                    self.logger.error(f"Measurement {i} failed for {container_name}: {measurement_error}")
                    measurements.append({
                        "timestamp": datetime.now().isoformat(),
                        "error": str(measurement_error)
                    })
            
            # Analyze trends
            trends = self._analyze_container_trends(measurements)
            
            return {
                "container": container_name,
                "measurements": measurements,
                "trends": trends,
                "duration_minutes": duration_minutes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Container monitoring failed for {container_name}: {e}")
            return {
                "container": container_name,
                "error": str(e),
                "measurements": measurements,
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_container_trends(self, measurements: List[Dict]) -> Dict:
        """Analyze trends in container measurements"""
        if len(measurements) < 2:
            return {"error": "insufficient_data"}
        
        # Filter out error measurements
        valid_measurements = [m for m in measurements if "error" not in m]
        
        if len(valid_measurements) < 2:
            return {"error": "insufficient_valid_data"}
        
        trends = {}
        
        for metric in ["cpu_percent", "memory_percent", "memory_usage_mb"]:
            values = [m.get(metric, 0) for m in valid_measurements]
            
            if len(values) >= 2:
                start_value = values[0]
                end_value = values[-1]
                avg_value = sum(values) / len(values)
                max_value = max(values)
                min_value = min(values)
                
                # Trend direction
                if end_value > start_value * 1.1:
                    direction = "increasing"
                elif end_value < start_value * 0.9:
                    direction = "decreasing"
                else:
                    direction = "stable"
                
                trends[metric] = {
                    "direction": direction,
                    "start_value": start_value,
                    "end_value": end_value,
                    "avg_value": round(avg_value, 2),
                    "max_value": max_value,
                    "min_value": min_value,
                    "change_percent": round(((end_value - start_value) / start_value) * 100, 2) if start_value > 0 else 0
                }
        
        return trends
    
    async def get_docker_system_info(self) -> Dict:
        """
        Get Docker system information
        """
        if not self.client:
            return {"error": "Docker client not available"}
        
        try:
            info = self.client.info()
            version = self.client.version()
            
            return {
                "docker_info": {
                    "containers": info.get("Containers", 0),
                    "containers_running": info.get("ContainersRunning", 0),
                    "containers_paused": info.get("ContainersPaused", 0),
                    "containers_stopped": info.get("ContainersStopped", 0),
                    "images": info.get("Images", 0),
                    "server_version": info.get("ServerVersion", "unknown"),
                    "storage_driver": info.get("Driver", "unknown"),
                    "total_memory": info.get("MemTotal", 0),
                    "cpu_count": info.get("NCPU", 0)
                },
                "docker_version": version,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Docker system info: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
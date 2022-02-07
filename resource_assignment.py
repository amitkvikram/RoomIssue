from audioop import mul
from importlib import resources
from re import S
import threading
from enum import Enum
from numpy import sort
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from sqlalchemy import alias
from torch import device
import itertools
import copy
from random import randint



class Device(str, Enum):
    cpu = "cpu"
    gpu = "gpu"


class DeviceInfo(BaseModel):
    server_name: str
    device_type: Device
    in_use: bool
    device_id: str


class ServerInfo(BaseModel):
    server_name: str
    device_type: Device
    device_ids: List[str]


class ResourceRepository:
    def __init__(self):
        self.mutex = threading.Lock()
        self.db_list = [
            DeviceInfo(server_name = 's1', device_type = 'cpu', in_use= False, device_id=0),
            DeviceInfo(server_name = 's1', device_type = 'gpu', in_use= False, device_id=1),
            DeviceInfo(server_name = 's1', device_type = 'gpu', in_use= False, device_id=0),
            DeviceInfo(server_name = 's2', device_type = 'cpu', in_use= False, device_id=0),
            DeviceInfo(server_name = 's2', device_type = 'gpu', in_use= False, device_id=1),
            DeviceInfo(server_name = 's2', device_type = 'gpu', in_use= False, device_id=0),
            DeviceInfo(server_name = 's3', device_type = 'cpu', in_use= False, device_id=0),
            DeviceInfo(server_name = 's3', device_type = 'gpu', in_use= False, device_id=1),
            DeviceInfo(server_name = 's3', device_type = 'gpu', in_use= False, device_id=0)
        ]
        self.resources: List[DeviceInfo] = self._fetch_all_from_db()

    def _is_empty(self):
        return len(self.resources) == 0

    def _fetch_all_from_db(self)->List[DeviceInfo]:
        return copy.deepcopy(self.db_list)

    def _update_db(self, resource: DeviceInfo):
        for resource_i in self.db_list:
            if resource_i.server_name == resource.server_name and resource_i.device_id == resource_i.device_id:
                resource_i.in_use = resource.in_use

    def free_resource(self, resource_in: ServerInfo):
        with self.mutex:
            for resource in self.resources:
                if (
                    resource.server_name == resource_in.server_name
                    and resource.device_type == resource_in.device_type
                    and resource.device_id in resource_in.device_ids
                ):
                    resource.in_use = False
                    self._update_db(resource)

    def _lock_resource(self, resource_in: ServerInfo):
        for resource in self.resources:
            if (
                resource.server_name == resource_in.server_name
                and resource.device_type == resource_in.device_type
                and resource.device_id in resource_in.device_ids
            ):
                resource.in_use = True
                self._update_db(resource)

    def _get_available_resources(
        self, resources: List[DeviceInfo], devices: List[Device], multi_gpu=False
    ) -> List[ServerInfo]:
        resources_out: List[ServerInfo] = []
        if multi_gpu:
            assert devices == [Device.gpu]
            resources_grouped = itertools.groupby(
                resources, lambda x: (x.server_name, x.device_type)
            )
            for (server_name, device_type), resource_list_gen in resources_grouped:
                resource_list = list(resource_list_gen)
                if device_type in devices:
                    device_ids = [resource_i.device_id for resource_i in resource_list]
                    server_in_use = any([resource_i.in_use for resource_i in resource_list])
                    if not server_in_use:
                        resources_out.append(
                            ServerInfo(
                                server_name=server_name,
                                device_type=device_type,
                                device_ids=device_ids,
                            )
                        )
        else:
            for resource in resources:
                if resource.device_type in devices and not resource.in_use:
                    resources_out.append(
                        ServerInfo(
                            server_name = resource.server_name, 
                            device_type = resource.device_type,
                            device_ids = [resource.device_id]
                        )
                    )
            resources_out = sorted(resources_out, key=lambda x: x.device_type == Device.cpu)
        return resources_out

    def assign_resource(
        self, devices: List[Device], multi_gpu: bool, lock_cpu: bool, refresh: bool=False
    ) -> Optional[ServerInfo]:
        if multi_gpu:
            assert devices == [Device.gpu]

        if refresh or self._is_empty():
            with self.mutex:
                self.resources = self._fetch_all_from_db()

        if lock_cpu:
            available_resources = self._get_available_resources(
                self.resources, devices, multi_gpu
            )
            if len(available_resources) > 0:
                with self.mutex:
                    available_resources = self._get_available_resources(
                        self.resources, devices, multi_gpu
                    )
                    if len(available_resources) > 0:
                        assigned_resource = available_resources[0]
                        self._lock_resource(assigned_resource)
                        return assigned_resource
            return None
        else:
            if Device.gpu in devices:
                """
                    This condition is for the tasks which can be run on both gpu and cpu,
                    and only if gpu is assigned then resource should be locked
                """
                available_resources = self._get_available_resources(
                    self.resources, [Device.gpu]
                )
                if len(available_resources) > 0:
                    with self.mutex:
                        available_resources = self._get_available_resources(
                            self.resources, [Device.gpu]
                        )
                        if len(available_resources) > 0:
                            assigned_resource = available_resources[0]
                            self._lock_resource(assigned_resource)
                            return assigned_resource

            cpu_resources = sorted(
                [
                    resource
                    for resource in self.resources
                    if resource.device_type == Device.cpu
                ],
                key=lambda x: x.in_use == True,
            )
            # print(cpu_resources)
            resource = cpu_resources[randint(0, len(cpu_resources) - 1)]
            assigned_resource = ServerInfo(
                            server_name = resource.server_name, 
                            device_type = resource.device_type,
                            device_ids = [resource.device_id]
                        )
            return assigned_resource


if __name__ == '__main__':
    resourceRepo = ResourceRepository()
    assigned_resource = resourceRepo.assign_resource(devices = ['cpu', 'gpu'], multi_gpu = False, lock_cpu=True)
    print("Assigned = ", assigned_resource)
    # print(resourceRepo.resources)

    assigned_resource = resourceRepo.assign_resource(devices = ['gpu'], multi_gpu = True, lock_cpu=True)
    print("Assigned = ", assigned_resource)
    # print(resourceRepo.resources)

    assigned_resource = resourceRepo.assign_resource(devices = ['cpu', 'gpu'], multi_gpu = False, lock_cpu=False)
    print("Assigned = ", assigned_resource)
    # print(resourceRepo.resources)

    assigned_resource = resourceRepo.assign_resource(devices = ['cpu', 'gpu'], multi_gpu = False, lock_cpu=False)
    print("Assigned = ", assigned_resource)
    # print(resourceRepo.resources)

    assigned_resource = resourceRepo.assign_resource(devices = ['cpu', 'gpu'], multi_gpu = False, lock_cpu=False)
    print("Assigned = ", assigned_resource)
    # print(resourceRepo.resources)

    assigned_resource = resourceRepo.assign_resource(devices = ['cpu', 'gpu'], multi_gpu = False, lock_cpu=False)
    print("Assigned = ", assigned_resource)

    assigned_resource = resourceRepo.assign_resource(devices = ['cpu', 'gpu'], multi_gpu = False, lock_cpu=False)
    print("Assigned = ", assigned_resource)

    assigned_resource = resourceRepo.assign_resource(devices = ['cpu', 'gpu'], multi_gpu = False, lock_cpu=False)
    print("Assigned = ", assigned_resource)

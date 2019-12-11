from cloudmesh.storage.StorageNewABC import StorageABC
from cloudmesh.mongo.DataBaseDecorator import DatabaseUpdate
from cloudmesh.common.debug import VERBOSE
from pprint import pprint
from pathlib import Path
from cloudmesh.common.console import Console


class Provider(StorageABC):

    def __init__(self, service=None, config="~/.cloudmesh/cloudmesh.yaml"):

        super(Provider, self).__init__(service=service, config=config)
        if self.kind == "local":
            from cloudmesh.storage.provider.local.Provider import \
                Provider as LocalProvider
            self.provider = LocalProvider(service=service, config=config)
        elif self.kind == "box":
            from cloudmesh.storage.provider.box.Provider import \
                Provider as BoxProvider
            self.provider = BoxProvider(service=service, config=config)
        elif self.kind == "gdrive":
            from cloudmesh.storage.provider.gdrive.Provider import \
                Provider as GdriveProvider
            self.provider = GdriveProvider(service=service, config=config)
        elif self.kind == "azureblob":
            from cloudmesh.storage.provider.azureblob.Provider import \
                Provider as AzureblobProvider
            self.provider = AzureblobProvider(service=service, config=config)
        elif self.kind == "awss3":
            from cloudmesh.storage.provider.awss3.Provider import \
                Provider as AwsProvider
            self.provider = AwsProvider(service=service, config=config)
        elif self.kind in ['google']:
            from cloudmesh.google.storage.Provider import \
                Provider as GoogleStorageProvider
            self.provider = GoogleStorageProvider(service=service,
                                                  config=config)
        else:
            raise ValueError(
                f"Storage provider '{self.service}' not yet supported")

    @DatabaseUpdate()
    def get(self, source=None, destination=None, recursive=False):
        """
        gets the content of the source on the server to the local destination

        :param source: the source file on the server
        :type source: string
        :param destination: the destination location ion teh local machine
        :type destination: string
        :param recursive: True if the source is a directory
                          and ned to be copied recursively
        :type recursive: boolean
        :return: cloudmesh cm dict
        :rtype: dict
        """

        d = self.provider.get(source=source, destination=destination,
                              recursive=recursive)
        return d

    @DatabaseUpdate()
    def put(self, source=None, destination=None, recursive=False):

        service = self.service
        d = self.provider.put(source=source, destination=destination,
                              recursive=recursive)
        return d

    @DatabaseUpdate()
    def create_dir(self, directory=None):

        service = self.service
        d = self.provider.create_dir(directory=directory)
        return d

    @DatabaseUpdate()
    def delete(self, source=None):
        """
        deletes the source

        :param source: The source
        :return: The dict representing the source
        """

        service = self.service
        d = self.provider.delete(source=source)
        # raise ValueError("must return a value")
        return d

    def search(self, directory=None, filename=None, recursive=False):

        d = self.provider.search(directory=directory, filename=filename,
                                 recursive=recursive)
        return d

    @DatabaseUpdate()
    def list(self, source=None, dir_only=False, recursive=False):

        d = self.provider.list(source=source, dir_only=dir_only,
                               recursive=recursive)
        return d

    def tree(self, source):

        data = self.provider.list(source=source)

        # def dict_to_tree(t, s):
        #    if not isinstance(t, dict) and not isinstance(t, list):
        #       print ("    " * s + str(t))
        #    else:
        #        for key in t:
        #            print ("    " * s + str(key))
        #            if not isinstance(t, list):
        #                dict_to_tree(t[key], s + 1)
        #
        # dict_to_tree(d, 0)

        pprint(data)

    # @DatabaseUpdate()
    def copy(self, source=None, destination=None, recursive=False):
        """
        Copies object(s) from source to destination
        :param source: "awss3:source_obj" the source is combination of
                        source CSP name and source object name which either
                        can be a directory or file
        :param destination: "azure:desti_obj" the destination is
                            combination of destination CSP and destination
                            object name which either can be a directory or file
        :param recursive: in case of directory the recursive refers to all
                          subdirectories in the specified source
        :return: dict
        """
        # Fetch CSP names and object names
        if source:
            source, source_obj = source.split(':')
        else:
            source, source_obj = None, None

        if destination:
            target, target_obj = destination.split(':')
        else:
            target, target_obj = None, None

        source_obj = str(Path(source_obj).expanduser())
        target_obj = str(Path(target_obj).expanduser())

        print(source, source_obj,target, target_obj)

        if source == "local":
            print(f"CALL PUT METHOD OF {self.kind} PROVIDER.")
            result = self.provider.put(source=source_obj,
                                       destination=target_obj,
                                       recursive=recursive)
            return result
        elif target == "local":
            print(f"CALL GET METHOD OF {self.kind} PROVIDER.")
            result = self.provider.get(source=source_obj,
                                       destination=target_obj,
                                       recursive=recursive)
            return result
        else:
            VERBOSE("Cloud to cloud copy", self.kind)

            target_kind = self.kind
            target_provider = self.provider
            config = "~/.cloudmesh/cloudmesh.yaml"

            print("target===> ", target_kind, target_provider)

            if source:
                super().__init__(service=source, config=config)
                source_kind = self.kind
                if source_kind == "azureblob":
                    from cloudmesh.storage.provider.azureblob.Provider import \
                         Provider as AzureblobProvider
                    source_provider = AzureblobProvider(service=source,
                                                        config=config)
                elif source_kind == "awss3":
                    from cloudmesh.storage.provider.awss3.Provider import \
                         Provider as AwsProvider
                    source_provider = AwsProvider(service=source, config=config)
                else:
                    return NotImplementedError

            print("source===> ", source_kind, source_provider)

            # get local storage directory
            super().__init__(service="local", config=config)
            local_storage = self.config[
                                    "cloudmesh.storage.local.default.directory"]

            local_target_obj = str(Path(local_storage).expanduser())
            source_obj = str(Path(source_obj).expanduser())

            print("local===> ", local_storage, local_target_obj)

            try:
                result = source_provider.get(source=source_obj,
                                             destination=local_target_obj,
                                             recursive=recursive)
                Console.ok(f"Fetched {source_obj} from {source} CSP")

                if (result and len(result[0]['fileName']) == 0) or \
                   len(result) == 0:
                    return Console.error(f"{source_obj} could not be found "
                                         f"in {source} CSP. Please check.")
            except Exception as e:
                return Console.error(f"Error while fetching {source_obj} from " 
                                     f"{source} CSP. Please check. {e}")
            else:
                source_obj = Path(local_target_obj) / source_obj
                print("upload =====> ",source_obj, target_obj)
                try:
                    result = target_provider.put(source=source_obj,
                                                 destination=target_obj,
                                                 recursive=recursive)
                    Console.ok(f"Copied {local_target_obj} to {target} CSP")

                    if result is None:
                        return Console.error(f"Error while copying {source_obj}"
                                             f" to {target} CSP. Source "
                                             f"object not found")
                    return result
                except Exception as e:
                    return Console.error(f"Error while copying {source_obj} to "
                                         f"{target} CSP. Please check. ", e)


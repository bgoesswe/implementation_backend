""" EO Data Discovery """
# TODO: Adding paging with start= maxRecords= parameter for record requesting 

from nameko.rpc import rpc, RpcProxy
from datetime import datetime
from typing import Union

from .schemas import ProductRecordSchema, RecordSchema, FilePathSchema
from .dependencies.csw import CSWSession, CWSError
from .dependencies.arg_parser import ArgParserProvider, ValidationError

import json
import logging



service_name = "data"


class ServiceException(Exception):
    """ServiceException raises if an exception occured while processing the 
    request. The ServiceException is mapping any exception to a serializable
    format for the API gateway.
    """

    def __init__(self, code: int, user_id: str, msg: str,
                 internal: bool=True, links: list=[]):
        self._service = service_name
        self._code = code
        self._user_id = user_id
        self._msg = msg
        self._internal = internal
        self._links = links

    def to_dict(self) -> dict:
        """Serializes the object to a dict.

        Returns:
            dict -- The serialized exception
        """

        return {
            "status": "error",
            "service": self._service,
            "code": self._code,
            "user_id": self._user_id,
            "msg": self._msg,
            "internal": self._internal,
            "links": self._links
        }


class DataService:
    """Discovery of Earth observation datasets that are available at the back-end.
    """

    name = service_name

    arg_parser = ArgParserProvider()
    csw_session = CSWSession()

    jobs_service = RpcProxy("jobs")

    deleted = False
    updatetime = None

    @rpc
    def get_all_products(self, user_id: str=None) -> Union[list, dict]:
        """Requests will ask the back-end for available data and will return an array of 
        available datasets with very basic information such as their unique identifiers.

        Keyword Arguments:
            user_id {str} -- The user id (default: {None})

        Returns:
             Union[list, dict] -- The products or a serialized exception
        """
        user_id = "openeouser"


        try:
            product_records = self.csw_session.get_all_products()
            response = ProductRecordSchema(many=True).dump(product_records)

            return {
                "status": "success",
                "code": 200,
                "data": response.data
            }
        except Exception as exp:
            return ServiceException(500, user_id, str(exp),
                links=["#tag/EO-Data-Discovery/paths/~1data/get"]).to_dict()

    @rpc
    def get_product_detail(self, user_id: str=None, name: str=None) -> dict:
        """The request will ask the back-end for further details about a dataset.

        Keyword Arguments:
            user_id {str} -- The user id (default: {None})
            name {str} -- The product identifier (default: {None})

        Returns:
            dict -- The product or a serialized exception
        """
        # Query Store addition:
        user_id = "openeouser"
        querydata = self.jobs_service.get_querydata_by_pid(name)
        orig_query = self.jobs_service.get_origquerydata_by_pid(name)
        dataset = self.jobs_service.get_dataset_by_pid(name)
        timestamp = self.jobs_service.get_querytimestamp_by_pid(name)

        result_set = None

        if querydata:
            pid = name
            name = dataset
        try:
            name = self.arg_parser.parse_product(name)
            product_record = self.csw_session.get_product(name)
            response = ProductRecordSchema().dump(product_record).data

            if result_set:
                response["input_files"] = result_set
            if querydata:
                response["query"] = querydata
                response.pop('spatial_extent', None)
                response.pop('temporal_extent', None)
                response.pop('bands', None)
                response["pid"] = "http://openeo.local.127.0.0.1.nip.io/collections/{}".format(pid)
                response["result"] = "http://openeo.local.127.0.0.1.nip.io/collections/{}/result".format(pid)
                response["execution-time"] = timestamp
                response["original_query"] = orig_query

            return {
                "status": "success",
                "code": 200,
                "data": response
            }
        except ValidationError as exp:
            return ServiceException(400, user_id, str(exp), internal=False,
                links=["#tag/EO-Data-Discovery/paths/~1collections~1{name}/get"]).to_dict()
        #except Exception as exp:
        #    return ServiceException(500, user_id, str(exp)).to_dict()

    @rpc
    def get_product_detail_filelist(self, user_id: str = None, name: str = None) -> dict:
        """The request will ask the back-end for further details about a dataset.

        Keyword Arguments:
            user_id {str} -- The user id (default: {None})
            name {str} -- The product identifier (default: {None})

        Returns:
            dict -- The product or a serialized exception
        """
        # Query Store addition:
        user_id = "openeouser"
        querydata = self.jobs_service.get_querydata_by_pid(name)
        dataset = self.jobs_service.get_dataset_by_pid(name)
        timestamp = self.jobs_service.get_querytimestamp_by_pid(name)

        result_set = None

        if querydata:
            pid = name
            result_set = self.jobs_service.reexecute_query(user_id, pid)
            name = dataset

        try:
            name = self.arg_parser.parse_product(name)
            product_record = self.csw_session.get_product(name)
            response = ProductRecordSchema().dump(product_record).data

            if result_set:
                response["input_files"] = result_set
            if querydata:
                response["query"] = querydata
                response.pop('spatial_extent', None)
                response.pop('temporal_extent', None)
                response.pop('bands', None)
                response["pid"] = "http://openeo.local.127.0.0.1.nip.io/collections/{}".format(pid)
                response["result"] = "http://openeo.local.127.0.0.1.nip.io/collections/{}/result".format(pid)
                response["execution-time"] = timestamp

            return {
                "status": "success",
                "code": 200,
                "data": response
            }
        except ValidationError as exp:
            return ServiceException(400, user_id, str(exp), internal=False,
                                    links=["#tag/EO-Data-Discovery/paths/~1collections~1{name}/get"]).to_dict()

    @rpc
    def get_product_detail_filelist_updated(self, user_id: str = None, name: str = None) -> dict:
        """The request will ask the back-end for further details about a dataset.

        Keyword Arguments:
            user_id {str} -- The user id (default: {None})
            name {str} -- The product identifier (default: {None})

        Returns:
            dict -- The product or a serialized exception
        """
        # Query Store addition:
        user_id = "openeouser"
        querydata = self.jobs_service.get_querydata_by_pid(name)
        dataset = self.jobs_service.get_dataset_by_pid(name)
        timestamp = self.jobs_service.get_querytimestamp_by_pid(name)

        result_set = None

        if querydata:
            pid = name
            result_set = self.jobs_service.reexecute_query(user_id, pid, deleted=True)
            name = dataset

        try:
            name = self.arg_parser.parse_product(name)
            product_record = self.csw_session.get_product(name)
            response = ProductRecordSchema().dump(product_record).data

            if result_set:
                response["input_files"] = result_set
            if querydata:
                response["query"] = querydata
                response.pop('spatial_extent', None)
                response.pop('temporal_extent', None)
                response.pop('bands', None)
                response["pid"] = "http://openeo.local.127.0.0.1.nip.io/collections/{}".format(pid)
                response["result"] = "http://openeo.local.127.0.0.1.nip.io/collections/{}/result".format(pid)
                response["execution-time"] = timestamp

            return {
                "status": "success",
                "code": 200,
                "data": response
            }
        except ValidationError as exp:
            return ServiceException(400, user_id, str(exp), internal=False,
                                    links=["#tag/EO-Data-Discovery/paths/~1collections~1{name}/get"]).to_dict()

    @rpc
    def get_records(self, user_id: str=None, name: str=None, detail: str="full", 
                    spatial_extent: str=None, temporal_extent: str=None, timestamp=None, updated=None,deleted=False) -> Union[list, dict]:
        """The request will ask the back-end for further details about the records of a dataset.
        The records must be filtered by time and space. Different levels of detail can be returned.

        Keyword Arguments:
            user_id {str} -- The user id (default: {None})
            detail {str} -- The detail level (full, short, file_paths) (default: {"full"})
            name {str} -- The product identifier (default: {None})
            spatial_extent {str} -- The spatial extent (default: {None})
            temporal_extent {str} -- The temporal extent (default: {None})

        Returns:
             Union[list, dict] -- The records or a serialized exception
        """
        # TODO: Filter by license -> see process get_data
        user_id = "openeouser"
        try:
            name = self.arg_parser.parse_product(name)

            # Parse the argeuments
            if spatial_extent:
                spatial_extent = self.arg_parser.parse_spatial_extent(spatial_extent)
            if temporal_extent:
                start, end = self.arg_parser.parse_temporal_extent(temporal_extent)
            else:
                start = None
                end = None

            # Retrieve records, based on detail level, and serialize
            response = []
            if detail == "full":
                response = self.csw_session.get_records_full(
                    name, spatial_extent, start, end)
            elif detail == "short":
                records = self.csw_session.get_records_shorts(
                    name, spatial_extent, start, end)
                response = RecordSchema(many=True).dump(records).data
            elif detail == "file_path":
                file_paths = self.csw_session.get_file_paths(
                    name, spatial_extent, start, end, timestamp, updated=updated, deleted=deleted)
                response = FilePathSchema(many=True).dump(file_paths).data

            return {
                "status": "success",
                "code": 200,
                "data": str(response)+": "+str(name)+" "+str(spatial_extent)+" "+str(start)+" "+str(end)
            }
        except ValidationError as exp:
            return ServiceException(400, user_id, str(exp), internal=False,
                links=["#tag/EO-Data-Discovery/paths/~1data~1{name}~1records/get"]).to_dict()
        except Exception as exp:
            return ServiceException(500, user_id, str(exp)).to_dict()

    @rpc
    def get_query(self, user_id: str = None, name: str = None, detail: str = "full",
                  spatial_extent: str = None, temporal_extent: str = None, timestamp=None,updated=False) -> dict:
        user_id = "openeouser"
        try:
            name = self.arg_parser.parse_product(name)

            # Parse the argeuments
            if spatial_extent:
                spatial_extent = self.arg_parser.parse_spatial_extent(spatial_extent)
            if temporal_extent:
                start, end = self.arg_parser.parse_temporal_extent(temporal_extent)
            else:
                start = None
                end = None

            if timestamp:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')

            orig_query = self.csw_session.get_query(
                name, spatial_extent, start, end, timestamp=str(timestamp))

            return {
                "status": "success",
                "code": 200,
                "data": str(orig_query)
            }
        except ValidationError as exp:
            return ServiceException(400, user_id, str(exp), internal=False,
                                    links=["#tag/EO-Data-Discovery/paths/~1data~1{name}~1records/get"]).to_dict()

    @rpc
    def updaterecord(self, process_graph: dict={}):
        user_id = "openeouser"
        try:
            if "updatetime" in process_graph:
                self.csw_session.set_updatetime(process_graph["updatetime"])
            if "deleted" in process_graph:
                self.csw_session.set_deleted(process_graph["deleted"])

            return {
                "status": "success",
                "code": 201,
                "headers": {"Location": ""}
            }
        except Exception as exp:
            return ServiceException(500, user_id, str(exp),
                                    links=["#tag/Job-Management/paths/~1jobs/post"]).to_dict()


    @rpc
    def set_deleted(self, deleted: bool):
        #logging.basicConfig(level=logging.DEBUG)

        #logging.info(deleted)
        #self.csw_session.set_deleted(deleted)
        state = None

        with open('mockup.json', 'r') as f:
            state = json.load(f)
        state["deleted"] = deleted
        with open('mockup.json', 'w') as fp:
            json.dump(state, fp)
        #self.deleted = deleted
        #logging.info(deleted)


    @rpc
    def set_updated(self, updated: str):
        #logging.basicConfig(level=logging.DEBUG)

        #logging.info(updated)
        state = None
        #self.csw_session.set_updatetime(updated)
        #self.updatetime = updated
        if updated:
            updated = datetime.utcnow()
            updated = updated.strftime('%Y-%m-%d %H:%M:%S.%f')
        #logging.info(self.updatetime)
        with open('mockup.json', 'r') as f:
            state = json.load(f)
        state["updatetime"] = updated
        with open('mockup.json', 'w') as fp:
            json.dump(state, fp)
        #logging.info(updated)


    @rpc
    def updatestate(self):
        """
            Returns the current version of the back end.
            :return: version_info: Dict of the current back end version.
        """


        state = None

        with open('mockup.json', 'r') as f:
            state = json.load(f)

        return {
            "status": "success",
            "code": 200,
            "data": state
        }

    def get_mockup_state(self):
        """
            Returns the current version of the back end.
            :return: version_info: Dict of the current back end version.
        """

        state = None

        with open('mockup.json', 'r') as f:
            state = json.load(f)

        return state
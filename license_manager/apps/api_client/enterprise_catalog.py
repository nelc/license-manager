from django.conf import settings

from license_manager.apps.api_client.base_oauth import BaseOAuthClient


class EnterpriseCatalogApiClient(BaseOAuthClient):
    """
    API client for calls to the enterprise catalog service.
    """
    api_base_url = settings.ENTERPRISE_CATALOG_URL + '/api/v1/'
    enterprise_catalog_endpoint = api_base_url + 'enterprise_catalogs/'
    distinct_catalog_queries_endpoint = api_base_url + 'distinct-catalog-queries/'

    def contains_content_items(self, catalog_uuid, content_ids):
        """
        Checks whether the specified enterprise catalog contains the given content.

        Arguments:
            catalog_uuid (UUID): UUID of the enterprise catalog to check.
            content_ids (list of str): List of content ids to check whether the catalog contains. The endpoint does not
                differentiate between course_run_ids and program_uuids so they can be used interchangeably. The two
                query parameters are left in for backwards compatability with edx-enterprise.

        Returns:
            bool: Whether the given content_ids were found in the specified enterprise catalog.
        """
        query_params = {'course_run_ids': content_ids}
        endpoint = self.enterprise_catalog_endpoint + str(catalog_uuid) + '/contains_content_items/'
        response = self.client.get(endpoint, params=query_params).json()
        return response.get('contains_content_items', False)

    def get_distinct_catalog_queries(self, enterprise_catalog_uuids):
        """
        Make a request to the distinct-catalog-queries endpoint to determine
        the number of distinct catalog queries used by SubscriptionPlans.

        Arguments:
            enterprise_catalog_uuids (list[UUID]): The list of EnterpriseCatalog UUIDs

        Returns:
            response (dict):
                count (int): number of distinct catalog query UUIDs used
                catalog_query_ids (list[int]): IDs of the catalog queries
        """
        request_data = {
            'enterprise_catalog_uuids': enterprise_catalog_uuids,
        }
        return self.client.post(
            self.distinct_catalog_queries_endpoint,
            json=request_data,
        ).json()

    def get_catalog_course_keys(self, catalog_uuid):
        endpoint = self.enterprise_catalog_endpoint + str(catalog_uuid)

        def get_course_keys(url):
            response = self.client.get(url).json()
            course_keys = [
                course['course_runs'][0]['key'] for course in response.get('results')
                if course.get('content_type') == 'course' and course['course_runs']
            ]

            if response.get('next'):
                course_keys += get_course_keys(response.get('next'))

            return course_keys

        return get_course_keys(endpoint)

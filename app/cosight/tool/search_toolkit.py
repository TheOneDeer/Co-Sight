# Copyright 2025 ZTE Corporation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Literal, Optional, TypeAlias, Union

import requests

from app.common.logger_util import logger

class SearchToolkit:
    r"""A class representing a toolkit for web search.

    This class provides methods for searching information on the web using
    search engines like Google, DuckDuckGo, Wikipedia and Wolfram Alpha, Brave.
    """

    def __init__(self):
        proxy = os.environ.get("PROXY")
        self.proxies = {"http": proxy, "https": proxy} if proxy else None

    def search_wiki(self, entity: str) -> str:
        r"""Search the entity in WikiPedia and return the summary of the
            required page, containing factual information about
            the given entity.

        Args:
            entity (str): The entity to be searched.

        Returns:
            str: The search result. If the page corresponding to the entity
                exists, return the summary of this entity in a string.
        """
        import wikipedia

        result: str

        try:
            result = wikipedia.summary(entity, sentences=5, auto_suggest=False)
        except wikipedia.exceptions.DisambiguationError as e:
            result = wikipedia.summary(
                e.options[0], sentences=5, auto_suggest=False
            )
        except wikipedia.exceptions.PageError:
            result = (
                "There is no page in Wikipedia corresponding to entity "
                f"{entity}, please specify another word to describe the"
                " entity to be searched."
            )
        except wikipedia.exceptions.WikipediaException as e:
            result = f"An exception occurred during the search: {e}"
        logger.info(f'search_wiki result = {result}')
        return result

    def search_linkup(
            self,
            query: str,
            depth: Literal["standard", "deep"] = "standard",
            output_type: Literal[
                "searchResults", "sourcedAnswer", "structured"
            ] = "searchResults",
            structured_output_schema: Optional[str] = None,
    ) -> Dict[str, Any]:
        r"""Search for a query in the Linkup API and return results in various
        formats.

        Args:
            query (str): The search query.
            depth (Literal["standard", "deep"]): The depth of the search.
                "standard" for a straightforward search, "deep" for a more
                comprehensive search.
            output_type (Literal["searchResults", "sourcedAnswer",
                "structured"]): The type of output:
                - "searchResults" for raw search results,
                - "sourcedAnswer" for an answer with supporting sources,
                - "structured" for output based on a provided schema.
            structured_output_schema (Optional[str]): If `output_type` is
                "structured", specify the schema of the output. Must be a
                string representing a valid object JSON schema.

        Returns:
            Dict[str, Any]: A dictionary representing the search result. The
                structure depends on the `output_type`. If an error occurs,
                returns an error message.
        """
        try:
            from linkup import LinkupClient

            # Initialize the Linkup client with the API key
            LINKUP_API_KEY = os.getenv("LINKUP_API_KEY")
            client = LinkupClient(api_key=LINKUP_API_KEY)

            # Perform the search using the specified output_type
            response = client.search(
                query=query,
                depth=depth,
                output_type=output_type,
                structured_output_schema=structured_output_schema,
            )

            if output_type == "searchResults":
                results = [
                    item.__dict__
                    for item in response.__dict__.get('results', [])
                ]
                return {"results": results}

            elif output_type == "sourcedAnswer":
                answer = response.__dict__.get('answer', '')
                sources = [
                    item.__dict__
                    for item in response.__dict__.get('sources', [])
                ]
                return {"answer": answer, "sources": sources}

            elif output_type == "structured" and structured_output_schema:
                return response.__dict__

            else:
                return {"error": f"Invalid output_type: {output_type}"}

        except Exception as e:
            logger.error(f'raise error: {str(e)}', exc_info=True)
            return {"error": f"An unexpected error occurred: {e!s}"}

    def search_duckduckgo(
            self, query: str, source: str = "text", max_results: int = 5
    ) -> List[Dict[str, Any]]:
        r"""Use DuckDuckGo search engine to search information for
        the given query.

        This function queries the DuckDuckGo API for related topics to
        the given search term. The results are formatted into a list of
        dictionaries, each representing a search result.

        Args:
            query (str): The query to be searched.
            source (str): The type of information to query (e.g., "text",
                "images", "videos"). Defaults to "text".
            max_results (int): Max number of results, defaults to `5`.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary
                represents a search result.
        """
        from duckduckgo_search import DDGS
        from requests.exceptions import RequestException

        ddgs = DDGS()
        responses: List[Dict[str, Any]] = []

        if source == "text":
            try:
                results = ddgs.text(keywords=query, max_results=max_results)
            except RequestException as e:
                # Handle specific exceptions or general request exceptions
                responses.append({"error": f"duckduckgo search failed.{e}"})

            # Iterate over results found
            for i, result in enumerate(results, start=1):
                # Creating a response object with a similar structure
                response = {
                    "result_id": i,
                    "title": result["title"],
                    "description": result["body"],
                    "url": result["href"],
                }
                responses.append(response)

        elif source == "images":
            try:
                results = ddgs.images(keywords=query, max_results=max_results)
            except RequestException as e:
                # Handle specific exceptions or general request exceptions
                responses.append({"error": f"duckduckgo search failed.{e}"})

            # Iterate over results found
            for i, result in enumerate(results, start=1):
                # Creating a response object with a similar structure
                response = {
                    "result_id": i,
                    "title": result["title"],
                    "image": result["image"],
                    "url": result["url"],
                    "source": result["source"],
                }
                responses.append(response)

        elif source == "videos":
            try:
                results = ddgs.videos(keywords=query, max_results=max_results)
            except RequestException as e:
                # Handle specific exceptions or general request exceptions
                responses.append({"error": f"duckduckgo search failed.{e}"})

            # Iterate over results found
            for i, result in enumerate(results, start=1):
                # Creating a response object with a similar structure
                response = {
                    "result_id": i,
                    "title": result["title"],
                    "description": result["description"],
                    "embed_url": result["embed_url"],
                    "publisher": result["publisher"],
                    "duration": result["duration"],
                    "published": result["published"],
                }
                responses.append(response)

        # If no answer found, return an empty list

        logger.info(f'search_duckduckgo result = {responses}')
        return responses

    def search_brave(
            self,
            q: str,
            country: str = "US",
            search_lang: str = "en",
            ui_lang: str = "en-US",
            count: int = 20,
            offset: int = 0,
            safesearch: str = "moderate",
            freshness: Optional[str] = None,
            text_decorations: bool = True,
            spellcheck: bool = True,
            result_filter: Optional[str] = None,
            goggles_id: Optional[str] = None,
            units: Optional[str] = None,
            extra_snippets: Optional[bool] = None,
            summary: Optional[bool] = None,
    ) -> Dict[str, Any]:
        r"""This function queries the Brave search engine API and returns a
        dictionary, representing a search result.
        See https://api.search.brave.com/app/documentation/web-search/query
        for more details.

        Args:
            q (str): The user's search query term. Query cannot be empty.
                Maximum of 400 characters and 50 words in the query.
            country (str): The search query country where results come from.
                The country string is limited to 2 character country codes of
                supported countries. For a list of supported values, see
                Country Codes. (default: :obj:`US `)
            search_lang (str): The search language preference. The 2 or more
                character language code for which search results are provided.
                For a list of possible values, see Language Codes.
            ui_lang (str): User interface language preferred in response.
                Usually of the format '<language_code>-<country_code>'. For
                more, see RFC 9110. For a list of supported values, see UI
                Language Codes.
            count (int): The number of search results returned in response.
                The maximum is 20. The actual number delivered may be less than
                requested. Combine this parameter with offset to paginate
                search results.
            offset (int): The zero based offset that indicates number of search
                results per page (count) to skip before returning the result.
                The maximum is 9. The actual number delivered may be less than
                requested based on the query. In order to paginate results use
                this parameter together with count. For example, if your user
                interface displays 20 search results per page, set count to 20
                and offset to 0 to show the first page of results. To get
                subsequent pages, increment offset by 1 (e.g. 0, 1, 2). The
                results may overlap across multiple pages.
            safesearch (str): Filters search results for adult content.
                The following values are supported:
                - 'off': No filtering is done.
                - 'moderate': Filters explicit content, like images and videos,
                    but allows adult domains in the search results.
                - 'strict': Drops all adult content from search results.
            freshness (Optional[str]): Filters search results by when they were
                discovered:
                - 'pd': Discovered within the last 24 hours.
                - 'pw': Discovered within the last 7 Days.
                - 'pm': Discovered within the last 31 Days.
                - 'py': Discovered within the last 365 Days.
                - 'YYYY-MM-DDtoYYYY-MM-DD': Timeframe is also supported by
                    specifying the date range e.g. '2022-04-01to2022-07-30'.
            text_decorations (bool): Whether display strings (e.g. result
                snippets) should include decoration markers (e.g. highlighting
                characters).
            spellcheck (bool): Whether to spellcheck provided query. If the
                spellchecker is enabled, the modified query is always used for
                search. The modified query can be found in altered key from the
                query response model.
            result_filter (Optional[str]): A comma delimited string of result
                types to include in the search response. Not specifying this
                parameter will return back all result types in search response
                where data is available and a plan with the corresponding
                option is subscribed. The response always includes query and
                type to identify any query modifications and response type
                respectively. Available result filter values are:
                - 'discussions'
                - 'faq'
                - 'infobox'
                - 'news'
                - 'query'
                - 'summarizer'
                - 'videos'
                - 'web'
                - 'locations'
            goggles_id (Optional[str]): Goggles act as a custom re-ranking on
                top of Brave's search index. For more details, refer to the
                Goggles repository.
            units (Optional[str]): The measurement units. If not provided,
                units are derived from search country. Possible values are:
                - 'metric': The standardized measurement system
                - 'imperial': The British Imperial system of units.
            extra_snippets (Optional[bool]): A snippet is an excerpt from a
                page you get as a result of the query, and extra_snippets
                allow you to get up to 5 additional, alternative excerpts. Only
                available under Free AI, Base AI, Pro AI, Base Data, Pro Data
                and Custom plans.
            summary (Optional[bool]): This parameter enables summary key
                generation in web search results. This is required for
                summarizer to be enabled.

        Returns:
            Dict[str, Any]: A dictionary representing a search result.
        """

        import requests

        BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Content-Type": "application/json",
            "X-BCP-APIV": "1.0",
            "X-Subscription-Token": BRAVE_API_KEY,
        }

        ParamsType: TypeAlias = Dict[
            str,
            Union[str, int, float, List[Union[str, int, float]], None],
        ]

        params: ParamsType = {
            "q": q,
            "country": country,
            "search_lang": search_lang,
            "ui_lang": ui_lang,
            "count": count,
            "offset": offset,
            "safesearch": safesearch,
            "freshness": freshness,
            "text_decorations": text_decorations,
            "spellcheck": spellcheck,
            "result_filter": result_filter,
            "goggles_id": goggles_id,
            "units": units,
            "extra_snippets": extra_snippets,
            "summary": summary,
        }

        response = requests.get(url, headers=headers, params=params, proxies=self.proxies)
        data = response.json()["web"]
        return data

    def search_google(
            self, query: str
    ) -> List[Dict[str, Any]]:
        r"""Use Google search engine to search information for the given query.

        Args:
            query (str): The query to be searched.
            num_result_pages (int): The number of result pages to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary
            represents a website.
                Each dictionary contains the following keys:
                - 'result_id': A number in order.
                - 'title': The title of the website.
                - 'description': A brief description of the website.
                - 'long_description': More detail of the website.
                - 'url': The URL of the website.

                Example:
                {
                    'result_id': 1,
                    'title': 'OpenAI',
                    'description': 'An organization focused on ensuring that
                    artificial general intelligence benefits all of humanity.',
                    'long_description': 'OpenAI is a non-profit artificial
                    intelligence research company. Our goal is to advance
                    digital intelligence in the way that is most likely to
                    benefit humanity as a whole',
                    'url': 'https://www.openai.com'
                }
            title, description, url of a website.
        """
        import requests

        # https://developers.google.com/custom-search/v1/overview
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        # https://cse.google.com/cse/all
        SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

        # Using the first page
        start_page_idx = 1
        # Different language may get different result
        search_language = "en"
        # How many pages to return
        num_result_pages = 3
        # Constructing the URL
        # Doc: https://developers.google.com/custom-search/v1/using_rest
        url = (
            f"https://www.googleapis.com/customsearch/v1?"
            f"key={GOOGLE_API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}&start="
            f"{start_page_idx}&lr={search_language}&num={num_result_pages}"
        )

        responses = []
        # Fetch the results given the URL
        try:
            # Make the get
            result = requests.get(url, proxies=self.proxies)
            data = result.json()

            # Get the result items
            if "items" in data:
                search_items = data.get("items")

                # Iterate over 10 results found
                for i, search_item in enumerate(search_items, start=1):
                    # Check metatags are present
                    if "pagemap" not in search_item:
                        continue
                    if "metatags" not in search_item["pagemap"]:
                        continue
                    if (
                            "og:description"
                            in search_item["pagemap"]["metatags"][0]
                    ):
                        long_description = search_item["pagemap"]["metatags"][
                            0
                        ]["og:description"]
                    else:
                        long_description = "N/A"
                    # Get the page title
                    title = search_item.get("title")
                    # Page snippet
                    snippet = search_item.get("snippet")

                    # Extract the page url
                    link = search_item.get("link")
                    response = {
                        "result_id": i,
                        "title": title,
                        "description": snippet,
                        "long_description": long_description,
                        "url": link,
                    }
                    responses.append(response)
            else:
                responses.append({"error": "google search failed."})

        except requests.RequestException:
            # Handle specific exceptions or general request exceptions
            responses.append({"error": "google search failed."})
        # If no answer found, return an empty list
        logger.info(f'search_google result = {responses}')
        return responses

    def query_wolfram_alpha(
            self, query: str, is_detailed: bool = False
    ) -> Union[str, Dict[str, Any]]:
        r"""Queries Wolfram|Alpha and returns the result. Wolfram|Alpha is an
        answer engine developed by Wolfram Research. It is offered as an online
        service that answers factual queries by computing answers from
        externally sourced data.

        Args:
            query (str): The query to send to Wolfram Alpha.
            is_detailed (bool): Whether to include additional details
                including step by step information in the result.
                (default: :obj:`False`)

        Returns:
            Union[str, Dict[str, Any]]: The result from Wolfram Alpha.
                Returns a string if `is_detailed` is False, otherwise returns
                a dictionary with detailed information.
        """
        import wolframalpha

        WOLFRAMALPHA_APP_ID = os.environ.get("WOLFRAMALPHA_APP_ID")
        if not WOLFRAMALPHA_APP_ID:
            raise ValueError(
                "`WOLFRAMALPHA_APP_ID` not found in environment "
                "variables. Get `WOLFRAMALPHA_APP_ID` here: `https://products.wolframalpha.com/api/`."
            )

        try:
            client = wolframalpha.Client(WOLFRAMALPHA_APP_ID)
            res = client.query(query)

        except Exception as e:
            logger.error(f'raise error: {str(e)}', exc_info=True)
            return f"Wolfram Alpha wasn't able to answer it. Error: {e}"

        pased_result = self._parse_wolfram_result(res)

        if is_detailed:
            step_info = self._get_wolframalpha_step_by_step_solution(
                WOLFRAMALPHA_APP_ID, query
            )
            pased_result["steps"] = step_info
            return pased_result

        return pased_result["final_answer"]

    def _parse_wolfram_result(self, result) -> Dict[str, Any]:
        r"""Parses a Wolfram Alpha API result into a structured dictionary
        format.

        Args:
            result: The API result returned from a Wolfram Alpha
                query, structured with multiple pods, each containing specific
                information related to the query.

        Returns:
            dict: A structured dictionary with the original query and the
                final answer.
        """

        # Extract the original query
        query = result.get("@inputstring", "")

        # Initialize a dictionary to hold structured output
        output = {"query": query, "pod_info": [], "final_answer": None}

        # Loop through each pod to extract the details
        for pod in result.get("pod", []):
            # Handle the case where subpod might be a list
            subpod_data = pod.get("subpod", {})
            if isinstance(subpod_data, list):
                # If it's a list, get the first item for 'plaintext' and 'img'
                description, image_url = next(
                    (
                        (data["plaintext"], data["img"])
                        for data in subpod_data
                        if "plaintext" in data and "img" in data
                    ),
                    ("", ""),
                )
            else:
                # Otherwise, handle it as a dictionary
                description = subpod_data.get("plaintext", "")
                image_url = subpod_data.get("img", {}).get("@src", "")

            pod_info = {
                "title": pod.get("@title", ""),
                "description": description,
                "image_url": image_url,
            }

            # For Results pod, collect all plaintext values from subpods
            if pod.get("@title") == "Results":
                results_text = []
                if isinstance(subpod_data, list):
                    for subpod in subpod_data:
                        if subpod.get("plaintext"):
                            results_text.append(subpod["plaintext"])
                else:
                    if description:
                        results_text.append(description)
                pod_info["description"] = "\n".join(results_text)

            # Add to steps list
            output["pod_info"].append(pod_info)

            # Get final answer
            if pod.get("@primary", False):
                output["final_answer"] = description

        return output

    def _get_wolframalpha_step_by_step_solution(
            self, app_id: str, query: str
    ) -> dict:
        r"""Retrieve a step-by-step solution from the Wolfram Alpha API for a
        given query.

        Args:
            app_id (str): Your Wolfram Alpha API application ID.
            query (str): The mathematical or computational query to solve.

        Returns:
            dict: The step-by-step solution response text from the Wolfram
                Alpha API.
        """
        # Define the base URL
        url = "https://api.wolframalpha.com/v2/query"

        # Set up the query parameters
        params = {
            "appid": app_id,
            "input": query,
            "podstate": ["Result__Step-by-step solution", "Show all steps"],
            "format": "plaintext",
        }

        # Send the request
        response = requests.get(url, params=params, proxies=self.proxies)
        root = ET.fromstring(response.text)

        # Extracting step-by-step steps, including 'SBSStep' and 'SBSHintStep'
        steps = []
        # Find all subpods within the 'Results' pod
        for subpod in root.findall(".//pod[@title='Results']//subpod"):
            # Check if the subpod has the desired stepbystepcontenttype
            content_type = subpod.find("stepbystepcontenttype")
            if content_type is not None and content_type.text in [
                "SBSStep",
                "SBSHintStep",
            ]:
                plaintext = subpod.find("plaintext")
                if plaintext is not None and plaintext.text:
                    step_text = plaintext.text.strip()
                    cleaned_step = step_text.replace(
                        "Hint: |", ""
                    ).strip()  # Remove 'Hint: |' if present
                    steps.append(cleaned_step)

        # Structuring the steps into a dictionary
        structured_steps = {}
        for i, step in enumerate(steps, start=1):
            structured_steps[f"step{i}"] = step

        return structured_steps

    def tavily_search(
            self, query: str, num_results: int = 5, **kwargs
    ) -> List[Dict[str, Any]]:
        r"""Use Tavily Search API to search information for the given query.

        Args:
            query (str): The query to be searched.
            num_results (int): The number of search results to retrieve
                (default is `5`).
            **kwargs: Additional optional parameters supported by Tavily's API:
                - search_depth (str): "basic" or "advanced" search depth.
                - topic (str): The search category, e.g., "general" or "news."
                - days (int): Time frame in days for news-related searches.
                - max_results (int): Max number of results to return
                  (overrides `num_results`).
                See https://docs.tavily.com/docs/python-sdk/tavily-search/
                api-reference for details.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing search
                results. Each dictionary contains:
                - 'result_id' (int): The result's index.
                - 'title' (str): The title of the result.
                - 'description' (str): A brief description of the result.
                - 'long_description' (str): Detailed information, if available.
                - 'url' (str): The URL of the result.
                - 'content' (str): Relevant content from the search result.
                - 'images' (list): A list of related images (if
                  `include_images` is True).
                - 'published_date' (str): Publication date for news topics
                  (if available).
        """
        from tavily import TavilyClient  # type: ignore[import-untyped]

        Tavily_API_KEY = os.getenv("TAVILY_API_KEY")
        if not Tavily_API_KEY:
            raise ValueError(
                "`TAVILY_API_KEY` not found in environment variables. "
                "Get `TAVILY_API_KEY` here: `https://www.tavily.com/api/`."
            )

        client = TavilyClient(Tavily_API_KEY)

        try:
            results = client.search(query, max_results=num_results, **kwargs)
            logger.info(f'tavily_search result = {results}')
            return results
        except Exception as e:
            logger.error(f'error": f"An unexpected error occurred: {str(e)}', exc_info=True)
            return [{"error": f"An unexpected error occurred: {e!s}"}]

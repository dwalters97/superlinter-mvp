import requests
from google.cloud import storage
import logger
from google.cloud import secretmanager
from tenacity import retry, wait_exponential, stop_after_attempt
import json
import datetime as dt
from datetime import datetime, timedelta
import ast
import re


def api_downloader(request):
    try:
        # get parameters for both GET and POST methods
        api_url = request.args["api_url"]
        api_source_name = request.args["api_source_name"]
        api_method = request.args["api_method"]
        root_element = request.args["root_element"]
        output_bucket = request.args["output_bucket"]
        output_folder = request.args["output_folder"]
        project_id = request.args["project_id"]
        api_secret_id = request.args["api_secret_id"]

        # get parameters for either GET or POST methods
        api_token_url = request.args["api_token_url"]
        api_advertiser_id = request.args["api_advertiser_id"]
        api_client_id = request.args["api_client_id"]
        api_json_body_str = request.args["api_json_body"]
        no_of_days = request.args["no_of_days"]
        api_start_date = request.args["api_start_date"]
        api_end_date = request.args["api_end_date"]

        # Convert API json body string to json object
        if api_method == "POST":
            api_json_body = json.dumps(ast.literal_eval(api_json_body_str))
        else:
            api_json_body = api_json_body_str

        # Local parameters
        param_dict = {}
        mandatory_param_dict = {}
        run_date = datetime.now().strftime("%Y%m%d")
        source_raw_file_name = "/tmp/" + api_source_name + "_api_raw_data.json"
        source_file_name = "/tmp/" + api_source_name + "_api_data.json"
        output_file = f"{api_source_name}_{run_date}.json"

        # Get API start and end dates if required.
        if (
            (api_method == "POST")
            and (no_of_days is not None and len(no_of_days.strip()) > 0)
            and (api_start_date is None or len(api_start_date.strip()) == 0)
        ):
            api_start_date = (
                datetime.now() - timedelta(days=int(no_of_days))
            ).strftime("%Y-%m-%d")
            api_end_date = datetime.now().strftime("%Y-%m-%d")
        else:
            api_start_date = api_start_date
            api_end_date = api_end_date

        # Perameters check for both GET and POST methods
        for variable in [
            "api_url",
            "api_source_name",
            "api_method",
            "root_element",
            "output_bucket",
            "output_folder",
            "project_id",
            "api_secret_id",
        ]:
            mandatory_param_dict[variable] = eval(variable)
        mandatory_param_check(mandatory_param_dict)

        # Perameters check for different possible scenarios in both GET and POST methods
        if api_method == "POST":
            if api_token_url is None or len(api_token_url.strip()) == 0:
                raise NameError("POST - Expected 'api_token_url' parameter is empty..")
            elif api_client_id is None or len(api_client_id.strip()) == 0:
                raise NameError("POST - Expected 'api_client_id' parameter is empty..")
            elif api_secret_id is None or len(api_secret_id.strip()) == 0:
                raise NameError(
                    "POST - Expected 'api_client_secret' parameter is empty.."
                )
            elif api_json_body is None or len(api_json_body.strip()) == 0:
                raise NameError("POST - Expected 'api_json_body' parameter is empty..")
        elif api_method == "GET":
            if api_secret_id is None or len(api_secret_id.strip()) == 0:
                raise NameError(
                    "POST - Expected 'api_secret_password' parameter is empty.."
                )
        else:
            logger.info("GET and POST mandatory value checks are completed...")

        if api_method == "POST":
            if "@api_start_date" in api_url or "@api_start_date" in api_json_body:
                if api_start_date is None or len(api_start_date.strip()) == 0:
                    raise NameError(f"Expected {api_start_date} parameter not found..")
                elif api_start_date is not None or len(api_start_date.strip()) > 0:
                    try:
                        dt.datetime.strptime(api_start_date, "%Y-%m-%d")
                    except ValueError:
                        raise ValueError(
                            "api_start_date - Incorrect date format, should be YYYY-MM-DD"
                        )
                else:
                    logger.info("POST API api_start_date - Check Completed..")
            else:
                logger.info("POST API api_start_date - Check Not Required..")
        else:
            if "@api_start_date" in api_url:
                if api_start_date is None or len(api_start_date.strip()) == 0:
                    raise NameError(f"Expected {api_start_date} parameter not found..")
                elif api_start_date is not None or len(api_start_date.strip()) > 0:
                    try:
                        dt.datetime.strptime(api_start_date, "%Y-%m-%d")
                    except ValueError:
                        raise ValueError(
                            "api_start_date - Incorrect date format, should be YYYY-MM-DD"
                        )
                else:
                    logger.info("API api_start_date - Check Completed..")
            else:
                logger.info("API api_start_date - Check Not Required..")

        if api_method == "POST":
            if "@api_end_date" in api_url or "@api_end_date" in api_json_body:
                if api_end_date is None or len(api_end_date.strip()) == 0:
                    raise NameError(f"Expected {api_end_date} parameter not found..")
                elif api_end_date is not None or len(api_end_date.strip()) > 0:
                    try:
                        dt.datetime.strptime(api_end_date, "%Y-%m-%d")
                    except ValueError:
                        raise ValueError(
                            "api_end_date - Incorrect date format, should be YYYY-MM-DD"
                        )
                else:
                    logger.info("POST API api_end_date - Check Completed..")
            else:
                logger.info("POST API api_end_date - Check Not Required..")
        else:
            if "@api_end_date" in api_url:
                if api_end_date is None or len(api_end_date.strip()) == 0:
                    raise NameError(f"Expected {api_end_date} parameter not found..")
                elif api_end_date is not None or len(api_end_date.strip()) > 0:
                    try:
                        dt.datetime.strptime(api_end_date, "%Y-%m-%d")
                    except ValueError:
                        raise ValueError(
                            "api_end_date - Incorrect date format, should be YYYY-MM-DD"
                        )
                else:
                    logger.info("API api_end_date - Check Completed..")
            else:
                logger.info("API api_end_date - Check Not Required..")

        if api_method == "POST" and "@api_advertiser_id" in api_json_body:
            if api_advertiser_id is None or len(api_advertiser_id.strip()) == 0:
                raise NameError(f"Expected {api_advertiser_id} parameter not found..")
            else:
                logger.info("API api_advertiser_id - Check Completed..")
        else:
            logger.info("API api_advertiser_id - Check Not Required..")

        # Create a dictionary to derive the API advertiser id, API start date and end date to the API endpoint and JSON body.
        for variable in ["api_start_date", "api_end_date", "api_advertiser_id"]:
            param_dict[variable] = eval(variable)

        # Get secret key for both GET and POST
        api_secret_key = get_secret_value(project_id, api_secret_id)

        api_url = replace_all_param(api_url, param_dict)

        if api_method == "POST":
            api_url = replace_all_param(api_url, param_dict)
            api_json_body_with_params = replace_all_param(api_json_body, param_dict)
        else:
            api_url = replace_all_param(api_url, param_dict)
            api_json_body_with_params = api_json_body

        if api_method == "POST":
            authorization = get_access_token(
                api_token_url, api_client_id, api_secret_key
            )
        else:
            authorization = api_secret_key

        # Invoke all other key functions, which downloads the files and load them into GCS
        get_data_from_api(
            api_url,
            authorization,
            api_json_body_with_params,
            api_method,
            source_raw_file_name,
        )
        convert_json_to_newline_json(
            source_raw_file_name, source_file_name, root_element
        )

        load_json_to_gcs(output_bucket, output_folder, output_file, source_file_name)

        return "SUCESS"

    except Exception as e:
        logger.error("Error in API Downloader method..")
        raise e


def mandatory_param_check(m_dict):
    try:
        for key, value in m_dict.items():
            if value is None or len(value.strip()) == 0:
                raise NameError(f"Expected {key} parameters not found..")
            else:
                logger.info(f"API {key} - Check Completed")
    except Exception as e:
        logger.error(f"Error in checking the mandatory parameters: {m_dict}")
        raise e


def replace_all_param(text, param_dict):
    try:
        for key, value in param_dict.items():
            text = text.replace("@" + key, value)
    except Exception as e:
        logger.error(
            f"Error in assigning the parameters: {text} with json body: {param_dict}"
        )
        raise e
    return text


def get_secret_value(project_id, secret_id):
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        logger.info("Secret Aquiring process is in progress - Open Connection")
        response = client.access_secret_version(request={"name": name})
        logger.info("Secret Aquiring process is in progress - Close Connection")
        secret_value = response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(
            f"Error in generating the secret key from projectid : {project_id}  and : {secret_id}."
        )
        raise e
    return secret_value


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=2))
def get_access_token(url, client_id, client_secret):
    token_response = requests.post(
        url, data={"grant_type": "client_credentials"}, auth=(client_id, client_secret)
    )
    if token_response.status_code != 200:
        raise NameError("Failed to obtain token from the OAuth 2.0 server")
    logger.info("Successfuly obtained a new token..")
    tokens = json.loads(token_response.text)
    return "Bearer " + tokens["access_token"]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=2))
def get_data_from_api(
    api_url, authorization, api_json_body_with_params, api_method, source_raw_file_name
):
    logger.info("Data pull from API - Running..")
    api_authorization = {
        "Content-Type": "application/json",
        "Authorization": authorization,
    }
    try:
        if (
            api_json_body_with_params is not None
            or api_json_body_with_params.strip() > 0
        ):
            # The response process is changed to batch downloader to avoid memory issues.
            with requests.request(
                api_method,
                api_url,
                headers=api_authorization,
                data=api_json_body_with_params,
            ) as response:
                with open(source_raw_file_name, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
            logger.info(
                f"Data pull from API - Completed and the row JSON file location is {source_raw_file_name}"
            )
        else:
            with requests.request(
                api_method, api_url, headers=api_authorization, stream=True
            ) as response:
                with open(source_raw_file_name, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
            logger.info(
                f"Data pull from API - Completed and the raw JSON file location is in {source_raw_file_name}"
            )
    except Exception as e:
        logger.error(
            f"Error in getting the data from API endpoint: {api_url} with json body: {api_json_body_with_params}"
        )
        raise e


def convert_json_to_newline_json(source_raw_file_name, source_file_name, root_element):
    try:
        # Convert JSON file into a new line JSON file using root element.
        with open(source_raw_file_name, encoding="utf-8-sig") as read_file:
            data = json.load(read_file)
        result = [record for record in data[root_element]]
        # Invoke Special Characters Cleanup function
        result = normalize_json(result)
        with open(source_file_name, "w") as obj:
            for rows in result:
                obj.write(json.dumps(rows) + "\n")

        logger.info(
            f"Data pull from API - Completed and the processd JSON file location is {source_file_name}"
        )
    except Exception as e:
        logger.error(
            f"Error in generation the newline json {source_file_name} file from {source_raw_file_name} using the {root_element} element"
        )
        raise e


def remove_special_characters_from_key(key):
    return re.sub("\W+", "_", key)  # noqa: W605


def normalize_json(result):
    try:
        array_list = []
        for r_array in result:
            array_list.append(
                {
                    remove_special_characters_from_key(key): value
                    for key, value in r_array.items()
                }
            )
        return array_list
    except Exception as e:
        logger.error(
            "Error in removeing the special charcter from key of the JSON file"
        )
        raise e


def upload_file_to_gcs(
    source_file_name, bucket_name, destination_folder, destination_blob_name
):
    """Uploads a file to the GCS bucket
    source_file_name (str) : name of source file
    bucket_name (str) : name of GCS bucket
    destination_folder (str) : folder in GCS bucket
    destination_blob_name (str) : file destination
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_folder + "/" + destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logger.info(
            "File {} uploaded to {}.".format(source_file_name, destination_blob_name)
        )
    except Exception as e:
        gs_msg = f"GSC upload failure: {e}"
        logger.exception(gs_msg)
        raise gs_msg


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=2))
def load_json_to_gcs(output_bucket, output_folder, output_file, source_file_name):
    logger.info("File upload to GCS - Running..")
    output_bucket = output_bucket
    output_folder = output_folder
    output_file = output_file
    source_file_name = source_file_name
    upload_file_to_gcs(source_file_name, output_bucket, output_folder, output_file)
    logger.info(
        f"File upload to GCS - Completed and the JSON file location in GCS is {output_bucket}/{output_folder}/{output_file} "
    )

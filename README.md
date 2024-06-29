# Clip Craft Backend

1. Clone the backend repo - 
git clone https://github.com/Louisljz/AI_Content_Creator_Backend.git -b ai-pipeline-fast-api-merge

# Local Setup
## Run "pip install -r requirements.txt" to install required dependencies
2. Open the project and install requirements with - 
pip install -r requirements.txt

## Then run "uvicorn main:app --reload --port <port-number>" to run the api on a specified port
3. Once dependencies are installed, run the command - 
uvicorn main:app --reload --port 8080
This will start the server on your machine on port 8080

## To run streamlit app run command "streamlit run app.py"
4. Query the upload-media endpoint at - 
http://localhost:8080/v1/upload-media

The upload-media endpoint takes in form-data in the body.
Formdata is like a json object in the sense that it has a key-value pair structure, but values can also hold files too

5. The required keys as of now are:
title, description, template, duration (in seconds btw), orientation (portrait/landscape)

6. Then additionally, there can be other key value pairs for files,
e.g; key: file_1, value: some_file

7. once the request body is ready, send the request to the upload-media endpoint.

8. The final video will be available as a link on a firebase bucket

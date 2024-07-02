# retell-custom-llm-python-demo

(This is a sample demo repo to show how to have your own LLM plugged into Retell.)

This repo currently uses `OpenAI` endpoint. Feel free to contribute to make
this demo more realistic.

This repos is intended to be used together with Simli Avatar API - found here [Link](https://github.com/simliai/simli-retell-frontend-reactjs-demo/tree/historicalCharacters). 

It also uses [unstructured.io](https://unstructured.io/) to process unstructered data and feed it into [Datastax astradb vector database](https://www.datastax.com/), which in turn is what is used to ensure that the interactions with historical characters are grounded in truth and historical context. 

We have a vector database that is public: `https://3cb6dbc5-f10f-43ba-9f2d-7af047ef7523-us-east1.apps.astra.datastax.com` that you can connect to by setting the ASTRA_ENDPOINT environment variable to that and ASTRA_TOKEN to our read-only token: `AstraCS:SxlTXLOHmGZawqimghkMDaeK:5c6cbc041fb72579587e5d933982704e728b9535148a250f9ce20c7518442d09` 

If you want to create your own, follow the steps below: 

## Create Your Own Vector Database
1. Generate structured .json data by running the script with a .pdf argument, for example:
One example of a historical source we used in this project is [this book about julius Caesar](https://dn790003.ca.archive.org/0/items/historyofjuliusc01napoiala/historyofjuliusc01napoiala.pdf)
```
UNSTRUCTURED_API_KEY=<YOUR_API_KEY> python3 unstructured/main.py <PDF FILE>
```

You can run this multiple times if you want to structure multiple files. 

2. Create a [Datastax account](https://accounts.datastax.com/session-service/v1/login) and create an AstraDB in the dashboard. 

3. Under "Integrations" on the left hand menu, enable OpenAI as embedding provider

4. Create a collection in your AstraDB called "caesar", for example.

5. Choose OpenAI as the embedding generation method

6. Upload the json files that you created in Step 1. 
## Steps to run custom LLM Websocket Server


1. First install dependencies

```bash
pip3 install -r requirements.txt
```

2. Fill out the API keys in `.env`

3. In another bash, use ngrok to expose this port to public network

```bash
ngrok http 8080
```

4. Start the websocket server

```bash
uvicorn app.server:app --reload --port=8080
```

You should see a fowarding address like
`https://dc14-2601-645-c57f-8670-9986-5662-2c9a-adbd.ngrok-free.app`, and you
are going to take the hostname `dc14-2601-645-c57f-8670-9986-5662-2c9a-adbd.ngrok-free.app`, prepend it with `wss://`, postpend with
`/llm-websocket` (the route setup to handle LLM websocket connection in the code) to create the url to use in the [dashboard](https://beta.retellai.com/dashboard) to create a new agent. Now
the agent you created should connect with your localhost.

The custom LLM URL would look like
`wss://dc14-2601-645-c57f-8670-9986-5662-2c9a-adbd.ngrok-free.app/llm-websocket`


5. Run Rag database queryer api:

```cd queryer```

```python main.py```

Note: the queryer code requires two environment variables set: ASTRA_TOKEN and ASTRA_ENDPOINT both which you can find in the AstraDB dashboard or use ours above if you are using our pubic vector database. 

This will start a fastapi that interfaces with datastax astradb, which is where we get the rag data to enrich the agent interactions.


## Run in prod

To run in prod, you probably want to customize your LLM solution, host the code
in a cloud, and use that IP to create agent.

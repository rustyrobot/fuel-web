
##Using an API for upgrade:

* [Get cluster (environment) information](#clusters1)
* [Setup cluster (environment) for upgrade](#clusters2)
* [Start cluster (environment) selected nodes upgrade](#clusters3)
* [Get information about available releases for upgrade](#releases)
* [Get information about nodes in the cluster](#nodes)

* Notes:
	* Don't forget to set ***X-Auth-Token*** header with token get from the keystone in the each API call.
	* If you're did not set ***X-Auth-Token*** header you will fail with ```401``` response code.

---

##<a name="clusters1">Get cluster (environment) information:</a>

* URL: ```/clusters```

* Method: ```GET```

* URL Params: ```None```

* Data Params: ```None```

* Success Response:
	* Code: ```200```
	* Content: ```JSON```
	* Sample Content: ```{ "id": 1, "status": "ready", "release_id": 2, "pending_release_id": null, ...
 }```

* Notes:
	* Possible values for ***"status"*** attribute: ***"operational"*** or ***"update"*** or ***"error"***

---

##<a name="clusters2">Setup cluster (environment) for upgrade:</a>

* URL: ```/clusters/<env_id> ```

* Method: ```PUT```

* URL Params (required):
	* env_id=[***integer***]: Id of the environment (cluster)

* Data Params (required):
	* Content: ```JSON```
	* Sample Content: ```{ "status": "update", "pending_release_id": 4 }```

* Success Response:
	* Code: ```200```
	* Content: ```JSON```
	* Sample Content: ```{ "id": 1, "status": "running", ... }```

* Notes:
	* On success call API should return JSON with same attributes set

---

##<a name="clusters3">Start cluster (environment) selected nodes upgrade:</a>

* URL: ```/clusters/<env_id>/deploy/?nodes=<node_id>,<node_id>,...,<node_id>```

* Method: ```PUT```

* URL Params (required):
	* env_id=[***integer***]: Id of the environment (cluster)
	* node_id=[***integer***]: Id of the selected node in the cluster (environment)

* Data Params (required):
	* Content: ```JSON```
	* Sample Content: ```{ }```

* Success Response:
	* Code: ```200```
	* Content: ```JSON```
	* Sample Content: ```{ "status": "running", "name": "deployment", ... }```

* Notes:
	* On success call API should return JSON with "***status***": "***running***", also all nodes "***status***" in the cluster should be changed to "***deploying***" and also changed their "***progress***" statuses.

---

##<a name="releases">Get information about available releases for upgrade:</a>

* URL: ```/releases```

* Method: ```GET```

* URL Params: ```None```

* Data Params: ```None```

* Success Response:
	* Code: ```200```
	* Content: ```JSON Array```
	* Sample Content:

~~~
		[
			{
				"id": 2,
				"name": "Icehouse on Ubuntu 12.04.4",
				"operating_system": "Ubuntu",
				"version": "2014.1.1-5.1",
				"state": "available",
				...
			},
			{
				...
			}
		]
~~~

* Notes:
	* Returned "***id***" of selected release should be used as "***pending\_release_id***"

---

##<a name="nodes">Get information about nodes in the cluster:</a>

* URL: ```/nodes```

* Method: ```GET```

* URL Params: ```None```

* Data Params: ```None```

* Success Response:
	* Code: ```200```
	* Content: ```JSON Array```
	* Sample Content:

~~~
		[
			{
				"id": "1",
				"status": "ready",
				"name": "Untitled (7e:61)",
				"roles": [ "controller", "mongo" ],
				"cluster": "1",
				"progress": "100",
				...
			},
			{
				...
			}
		]
~~~

* Notes
	* Returned "***status***" of each node may be: "***error***", "***ready***", "***deploying***", "***provisioned***"

---

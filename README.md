# Kube-escape

Exfiltrates a Kubernetes API server over a websocket connection.


This is useful when needing to connect to internal clusters where the API is
only reachable via a VPN you don't have access to, or via a slow Windows citrix VM.

This works by running a pod inside the kubernetes (or AKS, or ECS, or GKE, or..) cluster.

The pod needs the two following requirements:

- It should be able to talk with the Interweb (a webserver your control), on HTTP or HTTPs
- It should be able to talk with the kubernetes API (supposing that it is not filtered some way)


It will then create a websocket connection to your webserver (running the [proxy.py](proxy.py) proxy application).

In order to reach the k8s api from your non-corporate-approved laptop, you can use the [client.py](client.py) client.
You need to provide the websocket link given by the pod. Once launched, a bidirectional TCP socket will
be created from your machine to the kubernetes api, going through the websocket proxy, and the undercover pod.

Of course, you still need to have valid credentials, through a kubeconfig file


You'll need to edit the kubeconfig file and change the api host to be your localhost.



### Security

I guess you could proxy your websockets through an HTTPs endpoint. Wouldn't be bad.
However, the kubeapi proto is already over TLS, so it wouldn't add much value.

### Compression

Sadly it's not really possible (efficient-wise) to compress TLS data as it looks
random-ish.
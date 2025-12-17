
## Local Building and Testing
```bash
docker build -t runpod-pack . 
```
```bash
docker run runpod-pack
```

### Adding new tests
Inside `src`, create a new JSON input.
In `start.sh`, Add a call to rp_handler to run that JSON input. 

## Push to Docker Hub
```bash
docker tag runpod-pack jgeeslin/runpod-pack:latest
```

```bash
docker push jgeeslin/runpod-pack:latest
```
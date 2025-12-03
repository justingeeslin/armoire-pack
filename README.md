
## Local Building and Testing
```bash
docker build -t runpod-pack . 
```
```bash
docker run runpod-pack
```

## Push to Docker Hub
```bash
docker tag runpod-pack jgeeslin/runpod-pack:latest
```

```bash
docker push jgeeslin/runpod-pack:latest
```
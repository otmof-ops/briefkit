# Benchmarks and Evaluation

## Standard Benchmarks

NAS methods are typically evaluated on established benchmarks to ensure fair comparison:

| Benchmark | Task | Dataset | Metric |
|-----------|------|---------|--------|
| NAS-Bench-101 | Image Classification | CIFAR-10 | Test Accuracy |
| NAS-Bench-201 | Image Classification | CIFAR-10/100, ImageNet-16 | Test Accuracy |
| NAS-Bench-301 | Image Classification | CIFAR-10 | Predicted Accuracy |
| DARTS Search Space | Image Classification | CIFAR-10, ImageNet | Top-1/5 Accuracy |

## Results Comparison

According to Dong and Yang (2020), the top-performing architectures on NAS-Bench-201 achieve:

- **CIFAR-10**: 94.37% test accuracy
- **CIFAR-100**: 73.51% test accuracy
- **ImageNet-16**: 47.31% test accuracy

> The gap between the best NAS-found architecture and the optimal architecture in the search space is typically less than 0.5%, suggesting that modern NAS methods are highly effective at navigating large search spaces.

## Computational Cost

The training cost of NAS methods has decreased dramatically:

| Method | Year | GPU-Days | CIFAR-10 Accuracy |
|--------|------|----------|--------------------|
| NASNet | 2017 | 1800 | 96.59% |
| AmoebaNet | 2018 | 3150 | 96.66% |
| ENAS | 2018 | 0.5 | 96.13% |
| DARTS | 2019 | 1.0 | 97.00% |
| PC-DARTS | 2020 | 0.1 | 97.43% |

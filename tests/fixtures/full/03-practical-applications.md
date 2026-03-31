# Practical Applications

## Mobile and Edge Deployment

NAS has been particularly successful in designing efficient architectures for mobile and edge devices. **MnasNet** (Tan et al., 2019) and **EfficientNet** (Tan and Le, 2019) use NAS to optimise for both accuracy and latency.

| Model | Top-1 Accuracy | Latency (ms) | Parameters |
|-------|---------------|--------------|------------|
| MobileNetV2 | 72.0% | 6.9 | 3.4M |
| MnasNet-A1 | 75.2% | 7.8 | 3.9M |
| EfficientNet-B0 | 77.3% | 9.2 | 5.3M |
| EfficientNet-B7 | 84.3% | 183 | 66M |

## Natural Language Processing

Architecture search has been applied to transformer design:

- **Evolved Transformer** (So et al., 2019) found architectures that outperform the standard transformer on translation tasks
- **AutoTinyBERT** uses NAS to find efficient BERT variants for deployment

## Recommendations

Based on our analysis, we **recommend** the following approach for practitioners:

1. Start with a well-established search space (e.g., DARTS)
2. Use weight-sharing to reduce search cost
3. Always validate found architectures with full training from scratch
4. Consider hardware-aware NAS for deployment-specific optimisation

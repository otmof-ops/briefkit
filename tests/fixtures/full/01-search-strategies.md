# Search Strategies

## Reinforcement Learning-Based Search

The original NAS approach by Zoph and Le (2017) uses a **recurrent neural network controller** trained with reinforcement learning to generate architecture descriptions.

| Strategy | Search Cost | Performance | Scalability |
|----------|-------------|-------------|-------------|
| RL-based | High (800 GPU-days) | Excellent | Limited |
| Evolutionary | Medium (300 GPU-days) | Good | Moderate |
| Differentiable (DARTS) | Low (1 GPU-day) | Good | High |
| One-shot | Very Low (hours) | Moderate | Very High |

## Differentiable Architecture Search

**DARTS** (Liu et al., 2019) relaxes the discrete search space to be continuous, enabling gradient-based optimization. The key insight is that architecture selection can be treated as a continuous relaxation problem.

> Differentiable NAS reduced the computational barrier to architecture search by three orders of magnitude, democratising access to automated architecture design.

## Hyperparameters

| Hyperparameter | Typical Range | Impact |
|---------------|--------------|--------|
| Learning Rate | 0.001 - 0.1 | High |
| Search Epochs | 50 - 300 | Medium |
| Architecture Parameters LR | 0.0003 - 0.001 | High |
| Weight Decay | 1e-4 - 3e-4 | Low |
| Temperature (Gumbel-Softmax) | 0.1 - 1.0 | Medium |

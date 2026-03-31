# 3. Scaling Laws and Experimental Results

## 3.1 Neural Scaling Laws

Kaplan et al. (2020) established that language model cross-entropy loss follows precise power-law relationships with model parameters N, dataset size D, and training compute C. These relationships hold continuously across more than six orders of magnitude in N and eight orders of magnitude in C, with no detected saturation at the upper end.

The three primary scaling laws are:

```
L(N) = (N_c / N)^alpha_N      alpha_N = 0.076,  N_c = 8.8 x 10^13
L(D) = (D_c / D)^alpha_D      alpha_D = 0.095,  D_c = 5.4 x 10^13
L(C) = (C_c / C)^alpha_C      alpha_C = 0.057,  C_c = 1.6 x 10^7 PF-days
```

The exponents encode diminishing but reliable returns: each doubling of parameters reduces loss by approximately 5% (2^-0.076), each 10x increase in dataset size reduces loss by approximately 11%, and each 10x increase in compute reduces loss by approximately 12%. The consistency of these power laws across architectural configurations -- models from 2 to 207 layers, varying widths and depths -- suggests that the exponents are properties of the learning problem structure, not specific architecture choices.

A key finding is that model shape (depth vs. width ratio) has minimal impact on performance when total non-embedding parameter count is held constant. Embedding parameters are excluded from N because they contribute little to reasoning capacity despite comprising a significant fraction of total parameters (e.g., 103M of a 1B parameter model with a 50K vocabulary and 2048-dimensional embeddings).

Kaplan et al. drew a practical conclusion that proved influential but ultimately incorrect: given a fixed compute budget, most of that budget should be allocated to scaling model size rather than training data. Their analysis suggested N should scale as C^0.73 while D scales as C^0.27 -- meaning model size should increase roughly 5.5x faster than training tokens per compute doubling.

## 3.2 Chinchilla Optimal Compute

Hoffmann et al. (2022) overturned the Kaplan allocation with three independent estimation approaches, all converging on the same finding: for compute-optimal training, model size and training tokens should scale in equal proportion.

```
N_opt(C) proportional to C^0.5
D_opt(C) proportional to C^0.5
```

The operational rule: for every doubling of model size, double the number of training tokens. The optimal ratio is approximately 20 tokens per parameter. This directly contradicted prevailing practice. GPT-3 (175B parameters) was trained on 300B tokens -- roughly 12x fewer than the compute-optimal 3.7T tokens. Gopher (280B parameters) was trained on 300B tokens, approximately 20x fewer than the optimal 5.9T tokens. The entire generation of 2020-2022 frontier models was severely undertrained: they had far more parameters than their training data could effectively fill.

To validate this prediction, Hoffmann et al. trained Chinchilla: a 70B parameter model on 1.4 trillion tokens, using the same compute budget as the 280B parameter Gopher. Chinchilla outperformed Gopher on virtually every evaluation benchmark despite being 4x smaller, achieving 67.5% on MMLU compared to Gopher's 60.0% and 73.7% on HellaSwag compared to Gopher's 70.5%.

The Chinchilla result reshaped the training strategies of every major AI lab. LLaMA (Touvron et al., 2023), trained on 1.0-1.4T tokens for the 7B-65B parameter range, explicitly followed Chinchilla-optimal ratios. LLaMA-65B (65B parameters, 1.4T tokens) achieved 77.8% on HellaSwag and 63.4% on MMLU, competitive with Chinchilla at the same compute class.

## 3.3 Model Scaling Timeline

| Model | Year | Parameters | Training Tokens | Approx. Compute (FLOPs) | MMLU (5-shot) |
|-------|------|-----------|----------------|------------------------|---------------|
| GPT-1 | 2018 | 117M | ~5B | ~3.5 x 10^18 | -- |
| GPT-2 | 2019 | 1.5B | ~10B | ~9.0 x 10^19 | -- |
| GPT-3 | 2020 | 175B | 300B | 3.14 x 10^23 | 43.9% |
| Gopher | 2021 | 280B | 300B | 5.76 x 10^23 | 60.0% |
| Chinchilla | 2022 | 70B | 1.4T | 5.76 x 10^23 | 67.5% |
| PaLM | 2022 | 540B | 780B | 2.53 x 10^24 | 69.3% |
| LLaMA-65B | 2023 | 65B | 1.4T | ~5.5 x 10^23 | 63.4% |
| LLaMA-2-70B | 2023 | 70B | 2.0T | ~8.4 x 10^23 | 68.9% |
| GPT-4 | 2023 | ~1T+ (est.) | Undisclosed | Undisclosed | 86.4% |

Two patterns are immediately visible. First, the Chinchilla correction: post-2022 models are trained on dramatically more tokens per parameter than pre-2022 models. Second, MMLU scores improve with both scale and training data quality, but the relationship is nonlinear -- the jump from Gopher (60.0%) to Chinchilla (67.5%) came from training strategy alone, with identical compute.

## 3.4 Emergent Abilities at Scale

Wei et al. (2022) documented a distinct phenomenon: certain capabilities appear to emerge abruptly at specific model scales rather than improving gradually. Below a threshold scale, models perform at near-chance levels on specific tasks; above it, performance jumps discontinuously. Examples include:

- **Multi-step arithmetic**: GPT-3 models below 13B parameters achieve near-random accuracy on 3-digit addition; the 175B model achieves ~80% accuracy.
- **Word unscrambling**: Models below 6.7B parameters cannot unscramble words; performance appears at 13B+ parameters.
- **IPA transcription**: PaLM achieves near-zero accuracy below 62B parameters and ~40% at 540B parameters.

The emergent abilities finding remains debated. Schaeffer et al. (2023) argued that emergence is partly an artifact of metric choice -- nonlinear metrics (exact-match accuracy) produce apparent discontinuities, while linear metrics (token-level accuracy) show smooth scaling. Nevertheless, the empirical observation that qualitatively new capabilities appear at scale has profound implications for training resource allocation: a model slightly below a capability threshold may appear to have zero skill at a task, while a model slightly above it achieves useful performance.

## 3.5 Training Efficiency Comparisons

| Approach | Compute Budget (FLOPs) | MMLU | HellaSwag | Tokens per Parameter |
|----------|----------------------|------|-----------|---------------------|
| GPT-3 175B | 3.14 x 10^23 | 43.9% | 78.9% | 1.7 |
| Gopher 280B | 5.76 x 10^23 | 60.0% | 70.5% | 1.1 |
| Chinchilla 70B | 5.76 x 10^23 | 67.5% | 73.7% | 20.0 |
| LLaMA-65B | ~5.5 x 10^23 | 63.4% | 77.8% | 21.5 |
| LLaMA-2-70B | ~8.4 x 10^23 | 68.9% | 80.7% | 28.6 |

The tokens-per-parameter ratio is the clearest indicator of training efficiency. GPT-3 at 1.7 tokens per parameter was roughly 12x below optimal. Chinchilla at 20.0 tokens per parameter sits near the theoretical optimum. LLaMA-2 at 28.6 tokens per parameter deliberately overtrained relative to the Chinchilla optimum -- accepting higher training compute per parameter in exchange for a smaller, cheaper-to-serve model. This reflects a practical shift: the Chinchilla-optimal ratio minimizes training compute for a given performance level, but inference cost scales with parameter count. For deployment at scale, spending extra training compute to achieve target performance with fewer parameters is economically rational.

## 3.6 Open Questions

Several fundamental questions remain unresolved. The relationship between scaling laws and downstream task performance is not fully characterized -- cross-entropy loss improves smoothly with scale, but task-specific metrics do not always track loss monotonically. The extent to which scaling laws transfer across data distributions, languages, and modalities is partially validated but not comprehensively established. The irreducible entropy of natural language -- the theoretical floor below which no model can improve -- is estimated at approximately 0.9-1.0 nats per token for English, while current frontier models achieve roughly 1.5-1.7 nats, suggesting substantial room for improvement from scaling alone.

Perhaps most critically, the question of whether the power-law scaling regime will continue or eventually saturate remains empirically open. Every generation of models has extended the observed power-law relationship further, but there is no theoretical guarantee that it will hold indefinitely. The field's trillion-dollar investment thesis rests, in part, on the assumption that it will.

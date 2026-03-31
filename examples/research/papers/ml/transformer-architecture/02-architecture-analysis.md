# 2. Technical Architecture Analysis

## 2.1 Self-Attention Mechanism

The core operation of the transformer is scaled dot-product attention. Given input representations X of shape (n, d_model), three separate learned linear projections produce query, key, and value matrices:

```
Q = X W^Q    where W^Q in R^(d_model x d_k)
K = X W^K    where W^K in R^(d_model x d_k)
V = X W^V    where W^V in R^(d_model x d_v)
```

The attention output is computed as:

```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
```

The computation proceeds in five steps. First, raw compatibility scores S = QK^T are computed, producing an (n x n) matrix where S[i,j] is the dot product between query i and key j. Second, scores are scaled by 1/sqrt(d_k) to maintain unit variance -- without this, dot products grow proportionally to d_k, pushing the softmax into saturation regions where gradients vanish. For the base model with d_k = 64, this divides by 8. Third, optional causal masking sets future positions to negative infinity for autoregressive decoding. Fourth, row-wise softmax converts scores to attention weights A, where each row sums to 1. Fifth, the output is the weighted sum A * V, producing one d_v-dimensional vector per query position.

The separation of queries, keys, and values into three independent projections is architecturally essential. Queries determine what each position searches for; keys determine what each position advertises as its identity; values determine what each position contributes when attended to. A position's key and value can differ -- it might be highly matchable for "subject of sentence" queries while contributing "verb agreement" information through its value vector. This decoupling of "how to be found" from "what to contribute" gives the model representational flexibility that a single shared projection could not achieve.

### Multi-Head Attention

Rather than performing a single attention function with d_model-dimensional keys, queries, and values, multi-head attention runs h parallel attention operations with reduced dimensionality:

```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
where head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)
```

Each head operates on d_k = d_v = d_model / h dimensions. The base transformer uses h = 8 heads with d_k = d_v = 64 (given d_model = 512). The outputs are concatenated and linearly projected through W^O in R^(hd_v x d_model). Multi-head attention allows different heads to specialize: empirical analysis (Voita et al., 2019; Clark et al., 2019) has shown that individual heads learn distinct linguistic patterns -- syntactic dependencies, coreference resolution, positional relations -- without explicit supervision. The total parameter count and compute cost are equivalent to single-head attention with full dimensionality, but the representation quality is substantially higher.

## 2.2 Positional Encoding Strategies

Self-attention is permutation-equivariant: if input rows are permuted by matrix P, the output is permuted identically as P * MultiHead(X, X, X). This means "the cat sat" and "sat the cat" would produce identical output vectors, merely reordered. For natural language -- where word order carries semantic meaning -- explicit position information must be injected.

### Sinusoidal Encoding (Vaswani et al., 2017)

The original transformer uses fixed sinusoidal functions:

```
PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

Frequencies span from omega_0 = 1.0 (period ~6 positions, encoding fine positional detail) to omega_255 ~ 0.0001 (period ~62,000 positions, encoding coarse global position). The sine-cosine pairs define a rotation in 2D subspaces: for any fixed offset k, PE(pos + k) is a linear transformation of PE(pos) via a rotation matrix that depends only on k, not pos. This linear offset property enables the model to learn relative position reasoning through the Q and K projections.

### Learned Positional Embeddings

BERT, GPT-1, and GPT-2 use a learned embedding lookup table E_pos of shape (max_len, d_model). Each position gets a trainable vector. Empirically, learned embeddings match sinusoidal encodings on in-distribution performance (the original paper reports 25.7 vs 25.8 BLEU, within noise), but they cannot generalize beyond the maximum training length.

### Rotary Position Embeddings (RoPE)

Su et al. (2021) applied the rotation directly to query and key vectors before computing attention, making relative position encoding exact rather than approximate. The attention score between positions i and j becomes:

```
score(i, j) = (R(i) Q[i])^T (R(j) K[j]) / sqrt(d_k)
            = Q[i]^T R(j-i) K[j] / sqrt(d_k)
```

where R(k) is a block-diagonal rotation matrix parameterized by offset k. RoPE is the dominant positional encoding in modern large language models (LLaMA, Mistral, Gemini) due to its theoretical elegance and practical effectiveness for context length extension via interpolation techniques (YaRN, NTK-aware scaling).

### ALiBi (Attention with Linear Biases)

Press et al. (2022) proposed adding a linear bias -(i - j) * m to attention scores, where m is a head-specific slope. This penalizes long-range attention proportionally to distance, requiring no learned parameters and demonstrating strong length generalization. ALiBi is used in the MPT model family.

## 2.3 Feed-Forward Networks

Each transformer layer includes a position-wise feed-forward network applied independently to each position:

```
FFN(x) = max(0, x W_1 + b_1) W_2 + b_2
```

The inner dimension d_ff is typically 4 * d_model (2048 for the base model). The FFN acts as a per-position nonlinear transformation that processes the attention output. Recent work suggests FFNs function as key-value memories (Geva et al., 2021), where W_1 rows are keys matching input patterns and W_2 columns are corresponding value vectors recalled into the residual stream. Modern variants replace ReLU with GELU (Hendrycks & Gimpel, 2016) or SwiGLU (Shazeer, 2020), with SwiGLU providing consistent improvements of 0.5-1% on downstream benchmarks.

## 2.4 Layer Normalization and Residual Connections

The transformer uses residual connections around each sub-layer followed by layer normalization:

```
output = LayerNorm(x + Sublayer(x))
```

This is the "post-norm" configuration from the original paper. Residual connections enable gradient flow through deep stacks -- without them, gradients must propagate through every sub-layer transformation, compounding any contraction or expansion. With residuals, the gradient has a direct additive path from output to input.

**Pre-norm vs. post-norm.** The original post-norm placement (normalize after the residual addition) requires careful learning rate warmup to avoid training instability. Pre-norm (Xiong et al., 2020) places layer normalization before the sub-layer: output = x + Sublayer(LayerNorm(x)). Pre-norm training is more stable and does not require warmup, but produces slightly lower final quality in some settings. Most modern LLMs use pre-norm with RMSNorm (Zhang & Sennrich, 2019), which removes the mean-centering step for computational efficiency.

## 2.5 Computational Complexity Analysis

The fundamental bottleneck is the quadratic scaling of self-attention in sequence length. For a sequence of length n with hidden dimension d:

- **Attention score computation** (QK^T): O(n^2 d) FLOPs, O(n^2) memory for the attention matrix
- **Value aggregation** (AV): O(n^2 d) FLOPs
- **FFN computation**: O(n d d_ff) FLOPs = O(n d^2) since d_ff = 4d
- **Total per layer**: O(n^2 d + n d^2)

For short sequences (n < d), the FFN term O(n d^2) dominates -- attention is not the bottleneck. For long sequences (n > d), the attention term O(n^2 d) dominates, and the quadratic memory requirement for the (n x n) attention matrix becomes the binding constraint.

At n = 1024 with d = 512, attention cost is ~537M operations per layer. At n = 32,768 with d = 4096 (a modern LLM configuration), the attention matrix alone is ~1 billion entries -- 2 GB per layer in bfloat16. For a 32-layer model at batch size 1, this requires 64 GB solely for attention matrices, exceeding single-GPU memory.

### Attention Complexity Variants

| Method | Time Complexity | Memory | Exact? | Key Technique |
|--------|----------------|--------|--------|---------------|
| Standard attention | O(n^2 d) | O(n^2) | Yes | Full pairwise dot-product |
| Sparse attention (Longformer) | O(n w d) | O(n w) | Approx | Local window w + global tokens |
| LSH attention (Reformer) | O(n log n d) | O(n log n) | Approx | Locality-sensitive hashing buckets |
| Linear attention (Performer) | O(n d^2) | O(n d) | Approx | Kernel decomposition phi(Q)(phi(K)^T V) |
| FlashAttention | O(n^2 d) | O(n) | Yes | Tiled IO-aware computation |
| FlashAttention-2 | O(n^2 d) | O(n) | Yes | Optimized parallelism + work partitioning |
| Ring Attention | O(n^2 d / P) | O(n^2 / P) | Yes | Distributed across P devices |

The critical insight from FlashAttention (Dao et al., 2022) is that FLOP count is a poor proxy for wall-clock performance on memory-bound operations. Standard attention's bottleneck is not arithmetic -- it is HBM (high-bandwidth memory) access. On an A100 GPU, standard attention performs 66.6 GFLOPs with 40.3 GB of HBM reads/writes in 41.7 ms. FlashAttention performs 75.2 GFLOPs (more arithmetic due to recomputation) but only 4.4 GB of HBM traffic, completing in 7.3 ms -- a 5.7x speedup while performing strictly more FLOPs. This demonstrates that attention optimization must target memory access patterns, not operation counts.

## 2.6 The Residual Stream Perspective

A unifying view of the transformer, articulated by Elhage et al. (2021), interprets the d_model-dimensional representation at each position as a "residual stream." Each attention head and FFN sub-layer reads from this stream and writes an additive update back into it. The residual connection ensures that information is never destructively overwritten -- each sub-layer's contribution is additive. This perspective explains why transformers can be deep (information persists through residual connections), why attention heads can specialize (each reads and writes different subspaces), and why positional encodings injected at the input survive through all layers (the residual path preserves the original input additively through the entire network).

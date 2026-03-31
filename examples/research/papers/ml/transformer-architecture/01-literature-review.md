# 1. Literature Review: The Evolution of Transformer Architectures

## 1.1 Foundations: The Original Transformer

The transformer architecture emerged from a specific frustration with recurrent neural networks. Prior to 2017, dominant sequence transduction models -- LSTMs (Hochreiter & Schmidhuber, 1997), GRUs (Cho et al., 2014), and attention-augmented encoder-decoder RNNs (Bahdanau et al., 2015) -- processed sequences through a hidden state recurrence h_t = f(h_{t-1}, x_t) that was fundamentally sequential. Position t could not be computed until position t-1 finished. On modern parallel hardware, this sequential bottleneck left available compute underutilized.

Vaswani et al. (2017) proposed replacing recurrence entirely with self-attention. The key mechanism -- scaled dot-product attention, Attention(Q, K, V) = softmax(QK^T / sqrt(d_k))V -- computes pairwise compatibility between all positions in O(1) sequential steps regardless of sequence length. The original transformer used an encoder-decoder architecture with 6 layers each, 8 attention heads per layer, d_model = 512, and approximately 65 million parameters. On WMT 2014 English-to-German translation, it achieved 28.4 BLEU, surpassing the previous state of the art (ConvS2S; Gehring et al., 2017) by over 2 BLEU points while training in 3.5 days on 8 P100 GPUs.

The architectural contribution was not attention itself -- Bahdanau et al. had introduced neural attention in 2015 -- but demonstrating that attention as the sole mechanism, without recurrence or convolution, was sufficient for state-of-the-art sequence modeling.

## 1.2 Bidirectional Encoding: BERT

Devlin et al. (2019) introduced BERT (Bidirectional Encoder Representations from Transformers), which used only the transformer encoder stack with a masked language modeling (MLM) pre-training objective. Rather than predicting the next token autoregressively, BERT masked 15% of input tokens and trained the model to reconstruct them from bidirectional context. BERT-base comprised 12 layers, 12 attention heads, d_model = 768, and 110 million parameters; BERT-large scaled to 24 layers, 16 heads, d_model = 1024, and 340 million parameters.

BERT's bidirectional self-attention -- where every position attends to every other position without causal masking -- produced representations that encoded both left and right context simultaneously. This yielded dramatic improvements on downstream NLU benchmarks: BERT-large achieved 80.5% accuracy on MultiNLI, 93.5% F1 on SQuAD 2.0, and established new state-of-the-art results on all 11 GLUE tasks. The pre-train-then-fine-tune paradigm BERT established became the dominant transfer learning strategy for NLP.

Subsequent encoder variants refined the approach: RoBERTa (Liu et al., 2019) demonstrated that BERT was significantly undertrained and improved results by training longer with more data and dynamic masking. ALBERT (Lan et al., 2020) introduced cross-layer parameter sharing and factorized embedding parameterization to reduce parameters while maintaining performance. ELECTRA (Clark et al., 2020) replaced MLM with a replaced-token-detection objective for more efficient pre-training.

## 1.3 Autoregressive Decoding: The GPT Series

Radford et al. (2018) introduced GPT-1, a decoder-only transformer with 12 layers, 12 attention heads, and 117 million parameters, pre-trained on the BooksCorpus (approximately 800 million words) with a causal language modeling objective. GPT-1 demonstrated that generative pre-training followed by discriminative fine-tuning could achieve competitive results across diverse NLU tasks.

GPT-2 (Radford et al., 2019) scaled to 1.5 billion parameters (48 layers, 1600-dimensional embeddings, 25 attention heads) and was trained on WebText (40 GB of curated internet text, approximately 10 billion tokens). GPT-2 demonstrated zero-shot task transfer: without any fine-tuning, it achieved 55.0 F1 on CoQA and a perplexity of 35.76 on WikiText-103, competitive with supervised baselines.

GPT-3 (Brown et al., 2020) represented a qualitative shift. At 175 billion parameters (96 layers, 12,288-dimensional embeddings, 96 attention heads), trained on 300 billion tokens from a filtered Common Crawl mixture, GPT-3 exhibited strong few-shot learning. Given only a natural language task description and a handful of examples in the prompt, GPT-3 achieved 81.5% accuracy on HellaSwag, 76.2% on StoryCloze, and competitive performance on SuperGLUE -- without any gradient updates. The scale of compute was approximately 3.14 x 10^23 FLOPs.

InstructGPT (Ouyang et al., 2022) and GPT-4 (OpenAI, 2023) further refined the decoder-only paradigm through reinforcement learning from human feedback (RLHF) and instruction tuning, producing models that follow complex instructions and exhibit broad reasoning capabilities. GPT-4's architecture details remain undisclosed, though it is estimated to be a mixture-of-experts model in the range of 1--1.8 trillion total parameters.

## 1.4 Cross-Modal Applications: Vision Transformers

Dosovitskiy et al. (2021) applied the transformer architecture to image recognition with the Vision Transformer (ViT). Images are split into fixed-size patches (typically 16x16 pixels), linearly embedded, and treated as a sequence of tokens with a prepended [CLS] token. ViT-Large/16 (307 million parameters) achieved 87.76% top-1 accuracy on ImageNet after pre-training on JFT-300M, surpassing the state-of-the-art ResNet-based models (BiT-L; Kolesnikov et al., 2020).

The ViT result was significant because it demonstrated that transformers could match or exceed convolutional architectures on vision tasks without any image-specific inductive biases (no convolution, no pooling, no locality priors). Subsequent work extended the approach: DeiT (Touvron et al., 2021) introduced knowledge distillation and data augmentation strategies for training ViTs efficiently on ImageNet-1K alone. Swin Transformer (Liu et al., 2021) incorporated shifted windows for hierarchical feature maps and linear computational complexity in image size. DINO (Caron et al., 2021) demonstrated that self-supervised ViTs learn features that explicitly encode semantic segmentation without supervision.

## 1.5 Efficient Attention Mechanisms

The quadratic O(n^2) complexity of standard self-attention creates a computational bottleneck for long sequences. Several lines of work address this:

**Sparse attention patterns.** Longformer (Beltagy et al., 2020) combines local windowed attention with task-specific global attention tokens, reducing complexity to O(n). BigBird (Zaheer et al., 2020) adds random attention connections to the local + global pattern, achieving provable approximation guarantees.

**Reformer.** Kitaev et al. (2020) introduced locality-sensitive hashing (LSH) attention, which groups queries and keys into buckets using hash functions, restricting attention to within-bucket pairs. This reduces expected complexity to O(n log n). Reformer also introduced reversible residual layers to reduce memory from O(L) to O(1) in the number of layers.

**Linear attention.** Katharopoulos et al. (2020) reformulated attention by decomposing the softmax kernel as a feature map phi, yielding Attention(Q, K, V) = phi(Q)(phi(K)^T V) computable in O(n) time. The Performer (Choromanski et al., 2021) used random orthogonal features to approximate the softmax kernel, achieving unbiased linear-time attention with provable approximation bounds.

**Hardware-aware exact attention.** FlashAttention (Dao et al., 2022) took a fundamentally different approach: rather than approximating attention, it restructured the exact computation to minimize GPU HBM (high-bandwidth memory) accesses through tiling and recomputation. Standard attention requires Theta(Nd + N^2) HBM accesses; FlashAttention reduces this to Theta(N^2 d^2 M^-1), where M is SRAM size -- achieving 2-7.6x wall-clock speedup while computing mathematically identical results. FlashAttention-2 (Dao, 2023) further optimized parallelism and work partitioning for 2x additional speedup.

## 1.6 Comparison of Major Transformer Variants

| Model | Year | Parameters | Key Innovation | Primary Benchmark |
|-------|------|-----------|----------------|-------------------|
| Transformer | 2017 | 65M | Self-attention replaces recurrence | 28.4 BLEU (WMT EN-DE) |
| GPT-1 | 2018 | 117M | Generative pre-training + fine-tuning | 72.8% (avg. NLU tasks) |
| BERT-large | 2019 | 340M | Masked LM, bidirectional encoding | 80.5% (MultiNLI) |
| GPT-2 | 2019 | 1.5B | Zero-shot transfer via scale | 35.76 ppl (WikiText-103) |
| ViT-Large | 2021 | 307M | Image patches as tokens | 87.76% (ImageNet top-1) |
| GPT-3 | 2020 | 175B | In-context few-shot learning | 81.5% (HellaSwag) |
| Reformer | 2020 | -- | LSH attention, O(n log n) | Comparable to Transformer |
| Performer | 2021 | -- | Random feature linear attention | Comparable to softmax |
| Chinchilla | 2022 | 70B | Compute-optimal training ratio | 67.5% (MMLU) |
| LLaMA | 2023 | 7--65B | Open-source, efficient training | 77.8% (HellaSwag, 65B) |
| GPT-4 | 2023 | ~1T+ (est.) | MoE, RLHF, multimodal | 86.4% (MMLU) |

This progression reveals two persistent trends: the shift from encoder-decoder to decoder-only architectures for generative tasks, and the growing recognition that training data volume and quality matter as much as -- or more than -- raw parameter count.

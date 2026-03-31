# Transformer Architecture: A Survey of Innovations in Self-Attention Neural Networks

**Authors:** Research Group, University of Melbourne
**Keywords:** transformer, neural network, self-attention, positional encoding, scaling laws, training, attention mechanism, deep learning, epoch, AI/ML

## Abstract

The transformer architecture, introduced by Vaswani et al. (2017) in "Attention Is All You Need," has fundamentally restructured neural network design for sequence modeling and beyond. This survey traces the evolution of transformer architectures from the original encoder-decoder model through contemporary large-scale variants, examining four axes of innovation: self-attention mechanisms, positional encoding strategies, efficient attention approximations, and empirical scaling laws.

We review the progression from the original scaled dot-product attention through bidirectional encoders (BERT; Devlin et al., 2019), autoregressive decoders (GPT series; Radford et al., 2018--2023), and cross-modal applications (Vision Transformers; Dosovitskiy et al., 2021). We analyze the computational bottleneck imposed by quadratic attention complexity and survey approaches that address it, including sparse attention patterns (Longformer, BigBird), linear attention approximations (Performer, Reformer), and hardware-aware exact computation (FlashAttention; Dao et al., 2022). Finally, we examine scaling laws governing the relationship between model parameters, training data, and compute budget (Kaplan et al., 2020; Hoffmann et al., 2022), alongside emergent capabilities observed at scale (Wei et al., 2022). Our analysis synthesizes results across 40+ papers to identify persistent architectural principles and open research directions in transformer design.

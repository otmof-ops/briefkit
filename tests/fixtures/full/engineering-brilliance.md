# Engineering Brilliance

The most remarkable engineering achievement in NAS is the transition from brute-force search (thousands of GPU-days) to differentiable methods (single GPU-day) without sacrificing architecture quality. DARTS elegantly reformulates a discrete combinatorial problem as a continuous optimisation problem, enabling the use of gradient descent — the same tool that trains the networks themselves — to design them.

This represents a profound insight: the space of neural architectures is not fundamentally different from the space of neural network weights. Both can be navigated by gradients.

# Getting Started

## Installation

Install the Widget Framework via npm:

```bash
npm install @widgetcorp/framework
```

## Quick Start

Create your first widget in three lines:

```javascript
import { Widget } from '@widgetcorp/framework';

const hello = Widget.create('hello', {
  render: () => '<h1>Hello, Widgets!</h1>'
});
```

## Configuration

The framework supports the following configuration options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `debug` | boolean | false | Enable debug mode |
| `hotReload` | boolean | true | Enable hot-reloading in dev |
| `maxDepth` | number | 32 | Maximum component tree depth |
| `batchUpdates` | boolean | true | Batch state updates |

## Best Practices

- **Keep components small** — each widget should do one thing well
- **Use composition over inheritance** — prefer wrapping over extending
- **Avoid deep nesting** — flatten your component tree where possible

> Simplicity is the ultimate sophistication. A well-designed widget should be understandable at a glance.

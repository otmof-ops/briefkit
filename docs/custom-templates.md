# Custom Templates

Create custom templates by subclassing `BaseBriefingTemplate`.

## Setup

1. Create `.briefkit/templates/` in your project root
2. Add a Python file with your template class
3. Set `template.preset` in your config

## Example

```python
# .briefkit/templates/my_template.py
from briefkit.generator import BaseBriefingTemplate

class MyTemplate(BaseBriefingTemplate):
    name = "my_template"

    def build_story(self, content):
        """Override to control which sections appear and in what order."""
        story = []
        story.extend(self.build_cover(content))
        story.extend(self.build_toc(content))
        story.extend(self.build_executive_summary(content))
        story.extend(self.build_body(content))
        story.extend(self.build_custom_section("compliance-notes.md", content))
        story.extend(self.build_bibliography(content))
        return story
```

Then in config:

```yaml
template:
  preset: "my_template"
```

## Available Section Builders

All section builders are methods on `BaseBriefingTemplate`:

- `build_cover(content)` — cover page with title, subtitle, branding
- `build_classification_banner(content)` — level/navigation banner
- `build_toc(content)` — table of contents
- `build_executive_summary(content)` — summary from README overview
- `build_at_a_glance(content)` — metric dashboard
- `build_body(content)` — main content from numbered docs
- `build_cross_references(content)` — cross-reference map
- `build_key_terms(content)` — key terms index
- `build_bibliography(content)` — source bibliography
- `build_back_cover(content)` — back cover with branding
- `build_custom_section(filename, content)` — render a specific markdown file

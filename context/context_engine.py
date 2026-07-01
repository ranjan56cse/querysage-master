import logging


class ContextEngine:
    """Assembles prompt context with token budgeting, enforcing priorities and truncating lower priority items first."""

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def estimate_tokens(self, text: str) -> int:
        # Standard robust approximation: ~4 characters per token
        return max(1, len(text) // 4)

    def assemble_context(
        self,
        schema: str,
        ontology_rules: str,
        few_shot_examples: str,
        memory_patterns: str,
        user_query: str,
    ) -> str:
        """Assembles prompt elements, truncating lowest priority items first if budget (max_tokens) is exceeded.

        Priority order (highest to lowest):
        1. Schema (priority 1)
        2. Ontology Rules (priority 2)
        3. Few-shot Examples (priority 3)
        4. Memory Patterns (priority 4)
        5. User Query (priority 5)
        """
        components = [
            {"name": "Schema", "content": schema, "priority": 1},
            {"name": "Ontology Rules", "content": ontology_rules, "priority": 2},
            {"name": "Few-shot Examples", "content": few_shot_examples, "priority": 3},
            {"name": "Memory Patterns", "content": memory_patterns, "priority": 4},
            {"name": "User Query", "content": user_query, "priority": 5},
        ]

        # Calculate token estimates for each
        for comp in components:
            comp["tokens"] = self.estimate_tokens(comp["content"])

        total_tokens = sum(comp["tokens"] for comp in components)
        if total_tokens <= self.max_tokens:
            logging.info(
                f"Context assembled successfully within budget ({total_tokens}/{self.max_tokens} tokens)."
            )
            return "\n\n".join(f"### {c['name']}\n{c['content']}" for c in components)

        # Budget exceeded. Allocate to highest priority items first
        logging.warning(
            f"Context budget exceeded ({total_tokens}/{self.max_tokens} tokens). Budgeting priorities..."
        )
        budget_remaining = self.max_tokens
        assembled_parts = []

        # Sort by priority ascending (1 is highest priority, 5 is lowest)
        for comp in sorted(components, key=lambda x: x["priority"]):
            if budget_remaining <= 0:
                logging.warning(
                    f"Component '{comp['name']}' omitted entirely due to exhausted token budget."
                )
                continue

            comp_tokens = int(comp["tokens"])
            if comp_tokens <= budget_remaining:
                assembled_parts.append(f"### {comp['name']}\n{comp['content']}")
                budget_remaining -= comp_tokens
            else:
                # Truncate this component to fit the remaining budget
                allowed_chars = budget_remaining * 4
                truncated_content = (
                    comp["content"][:allowed_chars]
                    + "\n... [Remaining content truncated due to token budget limits]"
                )
                assembled_parts.append(f"### {comp['name']}\n{truncated_content}")
                logging.warning(
                    f"Component '{comp['name']}' truncated to fit remaining token budget ({budget_remaining} tokens)."
                )
                budget_remaining = 0

        return "\n\n".join(assembled_parts)

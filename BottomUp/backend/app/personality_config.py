AGENT_PERSONALITIES = {
    "frontend": [
        {"name": "UI_Designer", "style": "clean, accessible, semantic", "temperature": 0.0},
        {"name": "React_Engineer", "style": "component-based, hooks", "temperature": 0.1},
        {"name": "Styling_Expert", "style": "responsive, tailwind", "temperature": 0.1}
    ],
    "backend": [
        {"name": "API_Architect", "style": "RESTful endpoints, clear DTOs", "temperature": 0.0},
        {"name": "Auth_Expert", "style": "secure, JWT-based", "temperature": 0.0},
        {"name": "Logic_Specialist", "style": "modular business logic", "temperature": 0.1}
    ],
    "database": [
        {"name": "Schema_Designer", "style": "normalized schema, clear relations", "temperature": 0.0},
        {"name": "Query_Optimizer", "style": "indexing, efficient queries", "temperature": 0.1},
        {"name": "Migration_Engineer", "style": "safe migrations", "temperature": 0.0}
    ]
}

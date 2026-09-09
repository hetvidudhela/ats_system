"""
normalizer.py
=============
Centralized skill and keyword normalization for the ATS Engine.
Provides canonical naming, alias resolution, and false-positive prevention.
"""

import re
from typing import Optional

# Canonical skill definitions: canonical_id -> (Display Name, list of alias forms)
SKILL_TAXONOMY: dict[str, tuple[str, list[str]]] = {
    # Languages
    "python": ("Python", ["python", "python3", "python 3", "py"]),
    "javascript": ("JavaScript", ["javascript", "js", "ecmascript"]),
    "typescript": ("TypeScript", ["typescript", "ts"]),
    "java": ("Java", ["java", "core java", "java 8", "java 11", "java 17", "java 21"]),
    "c": ("C", ["c language", "c programming"]),  # 'c' alone is handled carefully via exact token
    "cpp": ("C++", ["c++", "cpp", "c plus plus"]),
    "csharp": ("C#", ["c#", "csharp", "c sharp", ".net c#"]),
    "golang": ("Go", ["golang", "go language"]),
    "php": ("PHP", ["php", "php7", "php8"]),
    "ruby": ("Ruby", ["ruby", "ruby on rails", "rails"]),
    "rust": ("Rust", ["rust", "rustlang"]),
    "swift": ("Swift", ["swift", "swiftui"]),
    "kotlin": ("Kotlin", ["kotlin"]),
    "dart": ("Dart", ["dart"]),
    "sql": ("SQL", ["sql", "structured query language", "ansi sql"]),
    "html": ("HTML", ["html", "html5"]),
    "css": ("CSS", ["css", "css3"]),
    "r": ("R", ["r language", "r programming"]),

    # Frameworks & Libraries
    "flutter": ("Flutter", ["flutter", "flutter framework"]),
    "react": ("React", ["react", "reactjs", "react.js", "react js"]),
    "react_native": ("React Native", ["react native", "react-native"]),
    "angular": ("Angular", ["angular", "angularjs", "angular.js", "angular 2+"]),
    "vue": ("Vue.js", ["vue", "vuejs", "vue.js", "vue 3"]),
    "nextjs": ("Next.js", ["nextjs", "next.js", "next js"]),
    "nodejs": ("Node.js", ["nodejs", "node.js", "node js", "node"]),
    "express": ("Express.js", ["express", "expressjs", "express.js"]),
    "fastapi": ("FastAPI", ["fastapi", "fast api"]),
    "django": ("Django", ["django", "django rest framework", "drf"]),
    "flask": ("Flask", ["flask"]),
    "spring_boot": ("Spring Boot", ["spring boot", "springboot", "spring framework", "spring"]),
    "dotnet": (".NET", [".net", "dotnet", "asp.net", ".net core", "asp.net core"]),

    # State Management & Architectural Patterns
    "provider": ("Provider", ["provider", "provider package"]),
    "bloc": ("BLoC", ["bloc", "flutter_bloc", "business logic component"]),
    "riverpod": ("Riverpod", ["riverpod"]),
    "redux": ("Redux", ["redux", "redux toolkit"]),
    "mvvm": ("MVVM", ["mvvm", "model view viewmodel", "model-view-viewmodel"]),
    "mvc": ("MVC", ["mvc", "model view controller"]),
    "microservices": ("Microservices", ["microservices", "microservice", "micro service architecture"]),

    # APIs & Communication
    "rest_api": ("REST API", ["rest api", "rest apis", "restful api", "restful apis", "restful", "rest"]),
    "graphql": ("GraphQL", ["graphql"]),
    "grpc": ("gRPC", ["grpc"]),
    "websockets": ("WebSockets", ["websocket", "websockets", "ws"]),

    # Databases & Storage
    "postgresql": ("PostgreSQL", ["postgresql", "postgres", "psql"]),
    "mysql": ("MySQL", ["mysql"]),
    "mongodb": ("MongoDB", ["mongodb", "mongo"]),
    "sqlite": ("SQLite", ["sqlite", "sqlite3"]),
    "redis": ("Redis", ["redis"]),
    "oracle": ("Oracle Database", ["oracle", "oracle db", "pl/sql", "plsql"]),
    "sql_server": ("SQL Server", ["sql server", "mssql", "microsoft sql server"]),
    "firebase": ("Firebase", ["firebase", "cloud firestore", "firestore", "firebase auth"]),
    "supabase": ("Supabase", ["supabase"]),
    "dynamodb": ("DynamoDB", ["dynamodb", "aws dynamodb"]),
    "elasticsearch": ("Elasticsearch", ["elasticsearch", "elastic search", "elk"]),

    # Cloud & DevOps
    "aws": ("AWS", ["aws", "amazon web services", "ec2", "s3", "lambda", "cloudformation"]),
    "gcp": ("GCP", ["gcp", "google cloud", "google cloud platform", "google cloud services"]),
    "azure": ("Azure", ["azure", "microsoft azure"]),
    "docker": ("Docker", ["docker", "dockerfile", "containerization", "containers"]),
    "kubernetes": ("Kubernetes", ["kubernetes", "k8s"]),
    "cicd": ("CI/CD", ["ci/cd", "cicd", "continuous integration", "continuous deployment"]),
    "git": ("Git", ["git", "github", "gitlab", "bitbucket", "version control"]),
    "linux": ("Linux", ["linux", "ubuntu", "debian", "centos", "unix", "bash", "shell scripting"]),
    "terraform": ("Terraform", ["terraform"]),
    "jenkins": ("Jenkins", ["jenkins"]),

    # Data & Machine Learning
    "machine_learning": ("Machine Learning", ["machine learning", "ml", "supervised learning", "unsupervised learning"]),
    "deep_learning": ("Deep Learning", ["deep learning", "neural networks"]),
    "nlp": ("Natural Language Processing", ["natural language processing", "nlp", "text processing"]),
    "pandas": ("Pandas", ["pandas"]),
    "numpy": ("NumPy", ["numpy"]),
    "scikit_learn": ("Scikit-Learn", ["scikit-learn", "scikit learn", "sklearn"]),
    "tensorflow": ("TensorFlow", ["tensorflow", "tf"]),
    "pytorch": ("PyTorch", ["pytorch"]),
    "power_bi": ("Power BI", ["power bi", "powerbi", "dax"]),
    "tableau": ("Tableau", ["tableau"]),
    "excel": ("Excel", ["excel", "advanced excel", "ms excel", "vlookup"]),

    # Methodologies & Tools
    "agile": ("Agile", ["agile", "scrum", "kanban", "sprint planning", "jira"]),
    "tdd": ("TDD", ["tdd", "test driven development", "test-driven development"]),
    "unit_testing": ("Unit Testing", ["unit testing", "unit tests", "pytest", "junit", "integration testing"]),
}

# Inverted index: normalized_alias -> canonical_id
ALIAS_MAP: dict[str, str] = {}
DISPLAY_NAMES: dict[str, str] = {}

for cid, (display, aliases) in SKILL_TAXONOMY.items():
    DISPLAY_NAMES[cid] = display
    for alias in aliases:
        ALIAS_MAP[alias.lower().strip()] = cid
    ALIAS_MAP[display.lower().strip()] = cid
    ALIAS_MAP[cid] = cid


def normalize_token(text: str) -> str:
    """
    Standard normalization for text comparison:
    Converts to lowercase, normalizes whitespace and hyphens,
    preserves critical technical characters (+, #, ., -).
    """
    if not text:
        return ""
    cleaned = text.lower().strip()
    # Normalize unicode quotes and dashes
    cleaned = cleaned.replace("–", "-").replace("—", "-")
    # Replace multiple spaces with a single space
    cleaned = re.sub(r"\s+", " ", cleaned)
    # Strip leading/trailing non-alphanumeric except for +, #, .
    cleaned = re.sub(r"^[^a-z0-9+#.]+|[^a-z0-9+#.]+$", "", cleaned)
    return cleaned.strip()


def resolve_canonical_skill(skill_str: str) -> Optional[tuple[str, str]]:
    """
    Given an arbitrary skill name, return (canonical_id, Display Name) if recognized.
    Returns None if not recognized in the taxonomy.
    Guards strictly against false positives.
    """
    norm = normalize_token(skill_str)
    if not norm:
        return None

    # Handle single character 'c' strictly
    if norm == "c":
        # Only resolve to C if explicitly 'c language', 'c programming' or standalone 'c'
        return ("c", "C")

    # Direct match in alias map
    if norm in ALIAS_MAP:
        cid = ALIAS_MAP[norm]
        return (cid, DISPLAY_NAMES[cid])

    # Try removing trailing 'js', '.js', 'framework', etc.
    simplified = re.sub(r"[\s.-]?(?:js|framework|library|tools?|technologies)$", "", norm).strip()
    if simplified and simplified in ALIAS_MAP:
        cid = ALIAS_MAP[simplified]
        return (cid, DISPLAY_NAMES[cid])

    return None


def get_display_name(skill_str: str) -> str:
    """
    Return canonical display name if known, else nicely formatted version of original.
    """
    res = resolve_canonical_skill(skill_str)
    if res:
        return res[1]
    # Default title-case fallback
    norm = skill_str.strip()
    if len(norm) <= 4 and norm.isupper():
        return norm
    return norm.title()

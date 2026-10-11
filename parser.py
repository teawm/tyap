import re
from enum import Enum
from typing import List, Optional, Any

# Типы токенов
class TokenType(Enum):
    NUMBER = 'NUMBER'
    ID = 'ID'
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    MUL = 'MUL'
    DIV = 'DIV'
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    EOF = 'EOF'

# Класс токена
class Token:
    def __init__(self, type_: TokenType, value: Any, position: int):
        self.type = type_
        self.value = value
        self.position = position
    
    def __repr__(self):
        return f"Token({self.type}, {self.value}, pos={self.position})"

# Лексический анализатор
class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.tokens = []
        self.token_splitter()
    ##
    def token_splitter(self) -> List[Token]:
        token_specification = [
            ('NUMBER',   r'\d+(\.\d+)?'),
            ('ID',       r'[a-zA-Z_][a-zA-Z_0-9]*'),
            ('PLUS',     r'\+'),
            ('MINUS',    r'-'),
            ('MUL',      r'\*'),
            ('DIV',      r'/'),
            ('LPAREN',   r'\('),
            ('RPAREN',   r'\)'),
            ('SKIP',     r'[ \t]+'),
        ]
        
        tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        
        for mo in re.finditer(tok_regex, self.text):
            kind = mo.lastgroup
            value = mo.group()
            position = mo.start()
            
            if kind == 'SKIP':
                continue
            elif kind == 'NUMBER':
                value = float(value) if '.' in value else int(value)
            elif kind == 'ID':
                value = value
            
            self.tokens.append(Token(TokenType[kind], value, position))
        
        self.tokens.append(Token(TokenType.EOF, None, len(self.text)))
        return self.tokens

# Узел дерева разбора
class ParseNode:
    def __init__(self, name: str, children: List[Any] = None):
        self.name = name
        self.children = children if children else []
    
    def add_child(self, child: Any):
        self.children.append(child)
    
    def __repr__(self):
        return f"ParseNode({self.name}, {self.children})"

# Синтаксический анализатор
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else None
        self.build_tree = False
    
    def error(self, message: str):
        """Генерирует ошибку с указанием позиции"""
        if self.current_token:
            print("    "," " * self.current_token.position, "^")
            raise SyntaxError(f"Ошибка в позиции {self.current_token.position}: {message}")
        else:
            raise SyntaxError(f"Ошибка: {message}")
    
    def match(self, expected_type: TokenType) -> Token:
        """Проверяет текущий токен и переходит к следующему"""
        if self.current_token.type == expected_type:
            token = self.current_token
            self.pos += 1
            self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None
            return token
        else:
            expected_names = {
                TokenType.NUMBER: "number",
                TokenType.ID: "id",
                TokenType.PLUS: "'+'",
                TokenType.MINUS: "'-'",
                TokenType.MUL: "'*'",
                TokenType.DIV: "'/'",
                TokenType.LPAREN: "'('",
                TokenType.RPAREN: "')'"
            }
            expected = expected_names.get(expected_type, str(expected_type))
            self.error(f"Ожидалось: {expected}, но получено: {self.current_token.type}")
    
    # Мейн функция парсера
    def parse(self, build_tree: bool = False) -> Optional[ParseNode]:
        self.build_tree = build_tree
        if self.build_tree:
            return self.parseS()
        else:
            self.parseS()
            if self.current_token.type != TokenType.EOF:
                self.error("Ожидался конец выражения")
            return None

    # S -> E
    def parseS(self) -> Optional[ParseNode]:
        if self.build_tree:
            node = ParseNode("S")
            node.add_child(self.parseE())
            if self.current_token.type != TokenType.EOF:
                self.error("Ожидался конец выражения")
            return node
        else:
            self.parseE()
            if self.current_token.type != TokenType.EOF:
                self.error("Ожидался конец выражения")
            return None
    
    # E -> T E'
    def parseE(self) -> Optional[ParseNode]:
        if self.build_tree:
            node = ParseNode("E")
            node.add_child(self.parseT())
            node.add_child(self.parseEPrime())
            return node
        else:
            self.parseT()
            self.parseEPrime()
            return None
    
    # E' -> + T E' | - T E' | ε
    def parseEPrime(self) -> Optional[ParseNode]:
        if self.build_tree:
            node = ParseNode("E'")
        
        if self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            if self.build_tree:
                op = self.match(self.current_token.type)
                node.add_child(ParseNode(f"OP: {op.value}"))
                node.add_child(self.parseT())
                node.add_child(self.parseEPrime())
                return node
            else:
                self.match(self.current_token.type)
                self.parseT()
                self.parseEPrime()
        else:
            if self.build_tree:
                node.add_child(ParseNode("ε"))
                return node
        
        return None if not self.build_tree else node
    
        # T -> F T'
    def parseT(self) -> Optional[ParseNode]:
        if self.build_tree:
            node = ParseNode("T")
            node.add_child(self.parseF())
            node.add_child(self.parseTPrime())
            return node
        else:
            self.parseF()
            self.parseTPrime()
            return None
    
    # T'  * F T' | / F T' | ε
    def parseTPrime(self) -> Optional[ParseNode]:
        if self.build_tree:
            node = ParseNode("T'")
        
        if self.current_token.type in (TokenType.MUL, TokenType.DIV):
            if self.build_tree:
                op = self.match(self.current_token.type)
                node.add_child(ParseNode(f"OP: {op.value}"))
                node.add_child(self.parseF())
                node.add_child(self.parseTPrime())
                return node
            else:
                self.match(self.current_token.type)
                self.parseF()
                self.parseTPrime()
        else:
            if self.build_tree:
                node.add_child(ParseNode("ε"))
                return node
        
        return None if not self.build_tree else node
    
    # F -> ( E ) | number | id
    def parseF(self) -> Optional[ParseNode]:
        if self.build_tree:
            node = ParseNode("F")
        
        if self.current_token.type == TokenType.LPAREN:
            if self.build_tree:
                node.add_child(ParseNode("("))
                self.match(TokenType.LPAREN)
                node.add_child(self.parseE())
                self.match(TokenType.RPAREN)
                node.add_child(ParseNode(")"))
                return node
            else:
                self.match(TokenType.LPAREN)
                self.parseE()
                self.match(TokenType.RPAREN)
        elif self.current_token.type == TokenType.NUMBER:
            if self.build_tree:
                node.add_child(ParseNode(f"NUM: {self.current_token.value}"))
            self.match(TokenType.NUMBER)
        elif self.current_token.type == TokenType.ID:
            if self.build_tree:
                node.add_child(ParseNode(f"ID: {self.current_token.value}"))
            self.match(TokenType.ID)
        else:
            self.error("Ожидалось: number, id или '('")
        
        return node if self.build_tree else None

# Функция для шикарнейшего вывода дерева
def print_tree(node: ParseNode, indent: str = ""):
    if node is None:
        return
    
    print(f"{indent}{node.name}")
    for child in node.children:
        if isinstance(child, ParseNode):
            print_tree(child, indent + "  ")
        else:
            print(f"{indent}  {child}")

# Мейн функция
def main():
    print("Синтаксический анализатор арифметических выражений")
    print("Введите выражение или 'exit' для выхода")
    print("Примеры: 2+3*4, a*(b-10), (7*2)")
    print("-" * 50)
    
    while True:
        try:
            text = input("\nВвод: ").strip()
            
            if text.lower() == 'exit':
                break
            
            if not text:
                continue
            
            # Лексический анализ
            lexer = Lexer(text)
            
            # Синтаксический анализ (без построения дерева)
            parser = Parser(lexer.tokens)
            parser.parse(build_tree=False)
            print("Вывод: Выражение корректно.")
            
            # Построение и вывод дерева
            print("\nДерево разбора:")
            parser2 = Parser(lexer.tokens)
            tree = parser2.parse(build_tree=True)
            print_tree(tree)
            
        except SyntaxError as e:
            print(f"Вывод: {e}")
        except Exception as e:
            print(f"Вывод: Ошибка! {e}")

# Тесты
def run_tests():
    test_cases = [
        ("2+3*4", True),
        ("a*(b-10)", True),
        ("5++3", False),
        ("(7*2", False),
        ("(2+3)*4", True),
        ("2+3*", False),
        ("x+y*z", True),
        ("((1+2))", True),
        ("1/(2+3)", True),
        ("a+b*c-d/e", False),
    ]
    
    print("Запуск тестов...")
    print("-" * 50)
    
    for text, expected in test_cases:
        try:
            lexer = Lexer(text)
            parser = Parser(lexer.tokens)
            parser.parse(build_tree=False)
            result = True
        except:
            result = False
        
        status = "\033[0;32m[✓]\033[0;37m" if result == expected else "\033[0;31m[✗]\033[0;37m"
        print(f"{status} '{text}' -> {'Корректно' if result else 'Ошибка'} (ожидалось: {'Корректно' if expected else 'Ошибка'})")
    print("Последний тест провальный исключительно для проверки красивого вывода тестов!")
if __name__ == "__main__":
    # Запустить тесты
    run_tests()
    print("\n" + "=" * 50 + "\n")
    # Запустить интерактивный режим
    main()
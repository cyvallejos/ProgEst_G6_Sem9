stack =[]

def push(item, capacity):
    if not is_full(capacity):
        stack.append(item)
        return "Elemento apilado..."
    return "Pila llena..."

def isEmpty():
    return not len(stack)

def is_full(capacity):
    return len(stack) == capacity

def peek():
    if not isEmpty():
        return stack[-1]
    return "Pila vacía..."

def pop_stack():
    if not isEmpty():
        return stack.pop()
    return "Pila vacía..."

def show():
    message = ""
    for item in reversed(stack):
        message += f" | {item: >6}|\n"
        message += f"└" + "─"* 8 + "┘\n"
    return message


capacity = int(input("Dime el tamaño de la pila: "))
while True:
    item = input("Dime un valor: ")
    print(push(item, capacity))
    answer = input("Desea ingresar otro dato [s | n]: ")
    if answer.lower() == "n":
        break

print("Mostrar tope")
print(peek())
print(peek())

print("Desapilar")
while True:
    answer = input("Desea desapilar [s | n]: ")
    if answer.lower() == "s":
        print(pop_stack())
    elif answer.lower() == "n":
        break
    else:
        print("Opción invalida...")
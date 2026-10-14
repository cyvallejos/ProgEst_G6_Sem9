#Crear un menú: apilar caja, desapilar, cosultar tope, mostrar pila y salir.
#No aceptar códigos vacíos ni duplicados.
#Mostrar cantidad de cajas y validar pila vacía.

cajas = []

while True:
	print("\n--- MENÚ DE CAJAS ---")
	print("1. Apilar caja")
	print("2. Desapilar caja")
	print("3. Consultar tope")
	print("4. Mostrar pila")
	print("5. Salir")

	opcion = input("Elige una opción: ").strip()

	if opcion == "1":
		codigo = input("Ingresa el código de la caja: ").strip()

		if not codigo:
			print("Error: el código no puede estar vacío.")
		elif codigo in cajas:
			print("Error: ese código ya está en la pila.")
		else:
			cajas.append(codigo)
			print("Caja apilada correctamente.")
			print(f"Cantidad de cajas: {len(cajas)}")

	elif opcion == "2":
		if not cajas:
			print("La pila está vacía; no hay cajas para desapilar.")
		else:
			codigo = cajas.pop()
			print(f"Caja desapilada: {codigo}")
			print(f"Cantidad de cajas: {len(cajas)}")

	elif opcion == "3":
		if not cajas:
			print("La pila está vacía; no hay caja en el tope.")
		else:
			print(f"Caja en el tope: {cajas[-1]}")

	elif opcion == "4":
		if not cajas:
			print("La pila está vacía.")
		else:
			print("Cajas en la pila (del tope hacia abajo):")
			for codigo in reversed(cajas):
				print(codigo)
		print(f"Cantidad de cajas: {len(cajas)}")

	elif opcion == "5":
		print("Saliendo del programa.")
		break

	else:
		print("Opción inválida. Elige un número del 1 al 5.")				
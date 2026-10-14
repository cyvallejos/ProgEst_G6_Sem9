#Al visitar una página nueva, conservar la anterior en una pila. Al regresar, extraer la última página guardada.
#Implementar: visitar, regresar, mostrar actual y mostrar historial.

historial = []
pila_regreso = []
pagina_actual = None

while True:
	print("\n--- MENÚ DE NAVEGACIÓN ---")
	print("1. Visitar página")
	print("2. Mostrar página actual")
	print("3. Mostrar historial")
	print("4. Salir")

	opcion = input("Elige una opción: ").strip()

	if opcion == "1":
		nueva_pagina = input("Ingresa la página que deseas visitar: ").strip()
		if not nueva_pagina:
			print("La página no puede estar vacía.")
		else:
			if pagina_actual is not None:
				pila_regreso.append(pagina_actual)
			pagina_actual = nueva_pagina
			print(f"Visitar: {pagina_actual}")
			while True:
				while True:
					guardar = input("¿Deseas guardar esta página en el historial? (s/n): ").strip().lower()
					if guardar in ("s", "n"):
						break
					print("Respuesta inválida. Escribe s o n.")

				if guardar == "s":
					historial.append(pagina_actual)
					print("Página guardada en el historial.")
				else:
					print("Página no guardada en el historial.")

				while True:
					respuesta = input("¿Deseas regresar a la página anterior? (s/n): ").strip().lower()
					if respuesta in ("s", "n"):
						break
					print("Respuesta inválida. Escribe s o n.")

				if respuesta == "s":
					if pila_regreso:
						pagina_actual = pila_regreso.pop()
						print(f"Regresar -> {pagina_actual}")
					else:
						print("Regresar -> sin anterior")
						break
				elif respuesta == "n":
					break
				else:
					print("Respuesta inválida. Escribe s o n.")

	elif opcion == "2":
		if pagina_actual is None:
			print("No hay una página actual.")
		else:
			print(f"Página actual: {pagina_actual}")

	elif opcion == "3":
		if historial:
			print("Historial de páginas visitadas (de la más reciente a la más antigua):")
			for pagina in reversed(historial):
				print(pagina)
		else:
			print("El historial está vacío.")

	elif opcion == "4":
		print("Saliendo del programa.")
		break

	else:
		print("Opción inválida. Elige un número del 1 al 4.")
from app.core.orchestrator import Orchestrator


def main():
    print("=" * 60)
    print("                     AURA")
    print("          AI Automation Assistant")
    print("=" * 60)
    print("Type 'exit' to quit.")
    print()

    try:
        aura = Orchestrator()
    except Exception as exc:
        print(f"Startup error: {exc}")
        return

    while True:

        try:
            user_input = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\n\nAURA: Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {
            "exit",
            "quit",
            "bye"
        }:
            print("AURA: Goodbye! 👋")
            break

        print("\nAURA: Thinking...\n")

        try:

            result = aura.run(user_input)

            response = result.get(
                "response",
                "I could not generate a response."
            )

            print(f"AURA: {response}")

        except Exception as exc:

            print(
                f"AURA: Something went wrong: {exc}"
            )

        print()


if __name__ == "__main__":
    main()
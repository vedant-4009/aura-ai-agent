from app.agent import run_agent


def main():
    print("=" * 60)
    print("AURA")
    print("Personal AI Automation Assistant")
    print("-" * 60)
    print("Web • Files • GitHub • AI Tools")
    print("Type 'exit' to quit")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nAURA: Goodbye!")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("\nAURA: Goodbye!")
            break

        if not user_input:
            continue

        try:
            answer = run_agent(user_input)
            print(f"\nAURA: {answer}")
        except Exception as exc:
            print(f"\nAURA Error: {exc}")


if __name__ == "__main__":
    main()
import typer

from codemodimportfrom import codemodimportfrom

cli = typer.Typer()


@cli.command()
def transform_importfrom(
    file_path: str,
    module: list[str] = typer.Option(default_factory=list),
    allow: list[str] = typer.Option(default_factory=list),
    transform_module_imports: bool = False,
    write: bool = False,
):
    if len(allow) == 1 and allow[0].endswith(".txt"):
        with open(allow[0]) as f:
            allow = [line.strip() for line in f if line.strip()]

    with open(file_path) as f:
        code = f.read()

    transformed_code = codemodimportfrom.transform_importfrom(
        code=code,
        modules=module,
        allow=allow,
        transform_module_imports=transform_module_imports,
    )

    if write:
        with open(file_path, "w") as f:
            f.write(transformed_code)
    else:
        print(transformed_code)


if __name__ == "__main__":
    cli()

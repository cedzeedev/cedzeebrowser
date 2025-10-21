
# Contribute to `cedzeebrowser`

If you wish to contribute to the project, I recommend focusing on the features outlined in the [TODO.md](TODO.md) and [issues](https://github.com/cedzeedev/cedzeebrowser/issues).

## Contribution Process

1. Fork this repository
2. Create a branch (`feature/my-new-feature`) (One feature = one Pull Request)
3. Commit your changes
4. Push your branch
5. Open a Pull Request

## Our Organization

**Minimal configuration**:

```txt
.
├── ...
├── main.py
├── src
│   └── *.py
├── offline
│   ├── ...
│   └── index.html
├───resources
│   |──...
│   └──icons
│       └── *.png
├── theme
│   ├── browser.css
│   └── theme.css
└── web
    └── *.html
```

## Coding Rules

> [!IMPORTANT]
>
> Please respect our [organization](#our-organization)
>

**Code style:**

- **Functions name**: snake_case (python only)
- **Class name**: CamelCase
- **Tabs**: 4 spaces
- **Constants**: FULL MAJ
- **⚠️**: Use [logger](src/ConsoleLogger.py) instead of `print`
- **Document your code using a comment** (`#` or `""" comment """`)

Please use [**Ruff formatter**](https://github.com/astral-sh/ruff)

Please, this project must be written in **Python**, **limit the use of other languages**.

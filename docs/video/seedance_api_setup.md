# Seedance 2.0 API Setup

## API Information

| Item         | Value                                                                |
| ------------ | -------------------------------------------------------------------- |
| Endpoint     | `POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks` |
| Model        | `doubao-seedance-2-0-260128`                                        |
| Auth         | `Authorization: Bearer ${ARK_API_KEY}`                               |
| Content-Type | `application/json`                                                   |

## Quick Start

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Set your API key in `.env`:

   ```
   ARK_API_KEY=your-actual-api-key
   ```

3. Install dependencies:

   ```bash
   pip install requests python-dotenv
   ```

4. Test configuration (no API charge):

   ```bash
   python scripts/test_seedance_config.py
   ```

5. Create a video task:

   ```python
   from scripts.seedance_client import load_config, create_video_task

   config = load_config()
   result = create_video_task("a cat walking on a beach", config=config)
   print(result)
   ```

## Security

**Never commit your `.env` file or hardcode your API key in source code.**

- `.env` is already listed in `.gitignore`.
- Use `.env.example` as the template for other developers.
- Rotate your API key if it is accidentally exposed.

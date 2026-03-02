# Conversation Toolkit Frontend

A customizable frontend for conversational applications. This repository provides a base implementation that can be easily modified and extended.

## Getting Started

### Forking & Setting Upstream

To customize this frontend while keeping the ability to pull updates from the original repository, the best approach is to **fork** it and set the upstream repository.

1. **Fork the repository** via GitLab UI.
2. **Clone your fork**:
   ```
   git clone https://gitlab.datascience.ch/industry/common/conversational-toolkit-frontend.git
   cd conversational-toolkit-frontend
   ```
3. **Set upstream to track the original repository**:
   ```
   git remote add upstream https://gitlab.datascience.ch/industry/common/conversational-toolkit-frontend.git
   ```
4. **Pull updates from upstream** (when needed):
   ```
   git fetch upstream
   git merge upstream/main
   ```

## Installation

Ensure you have [Node.js](https://nodejs.org/) and npm installed. Then, install dependencies:

```
npm install
```

## Development

### Running the Development Server

Start the development server:

```
npm run dev
```

This will launch the application at `http://localhost:3000`.

To run the development server with mock services, use:

```
npm run dev:mock
```

### Linting

To maintain code consistency, run:

```
npm run lint
```

## Building the Project

To generate a production build:

```
npm run build
```

This will create a `dist` folder containing the compiled static files. The build process uses `BUILD_MODE=export` to optimize the output.

Once built, you can copy these files into the root of your backend service, which will serve the frontend assets.

## Customization

You can modify the following files to tailor the frontend to your needs:

- **Branding & Theming**
    - `/public/`: Replace logo assets and favicon.
    - `/src/styles/global.css`: Modify theme colors and styles.

- **Configuration**
    - `/src/config.ts`: Update the agent name, page title, description, and logo path.
    - `/src/lib/lang/`: Customize default prompt suggestions and popup descriptions.

## Configuration

If the project requires specific environment variables, add them to a `.env` file:

```
# .env
SERVER_URL=https://your-backend-url.com
```

## Contributing

If you’d like to contribute improvements, submit a merge request! For major changes, please open an issue to discuss first.

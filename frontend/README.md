# SharinMod Frontend

A Next.js frontend application for the SharinMod platform - a token sharing system for AI models.

## Features

- **User Authentication**: Register and login with email/password
- **Token Sharing**: Share your bigmodel and z.ai API tokens with the community
- **Token Discovery**: Browse and discover tokens shared by other users
- **Unified Tokens**: Create unified tokens by combining multiple shared tokens
- **Token Consumption**: Use unified tokens to make API calls to AI models through a chat interface
- **Profile Management**: Update your user profile and bio
- **Usage History**: View your token usage history and statistics

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI primitives with custom components
- **State Management**: Zustand with persistence
- **API Client**: Axios with interceptors
- **Forms**: React Hook Form (planned for complex forms)

## Supported Vendors

- **bigmodel**: https://open.bigmodel.cn/v1 (model: glm-4.7)
- **z.ai**: https://z.ai/v1 (model: glm-4.7)

## Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up environment variables**:
   Create a `.env.local` file in the root directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser** and navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
src/
├── app/                    # Next.js app router pages
│   ├── dashboard/         # Main dashboard with token management
│   ├── login/            # Login page
│   ├── register/         # Registration page
│   └── chat/             # Chat interface for token consumption
├── components/           # Reusable UI components
│   ├── ui/              # Base UI components (buttons, inputs, etc.)
│   └── ...              # Feature-specific components
├── lib/                 # Utility libraries
│   ├── api.ts          # Axios client configuration
│   ├── services.ts     # API service functions
│   └── store.ts        # Zustand state management
└── types/              # TypeScript type definitions
```

## Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build the application for production
- `npm run start` - Start the production server
- `npm run lint` - Run ESLint for code linting

## API Integration

The frontend integrates with the SharinMod backend API. Make sure the backend is running and accessible at the URL specified in `NEXT_PUBLIC_API_URL`.

## Authentication

The app uses JWT tokens for authentication, stored securely in localStorage with automatic API header injection. Invalid tokens trigger automatic logout and redirect to login.

## Security Features

- Token encryption for secure storage
- Privacy protection in token discovery (anonymized usernames)
- JWT-based authentication with automatic logout on 401 responses
- Input validation and error handling

## Contributing

1. Follow the existing code style and patterns
2. Add proper TypeScript types
3. Include error handling for API calls
4. Test components and functionality
5. Update documentation as needed

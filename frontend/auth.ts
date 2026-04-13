import NextAuth from "next-auth";

import GitHub from "next-auth/providers/github";

const allowedEmails = process.env.ALLOWED_EMAILS
  ? process.env.ALLOWED_EMAILS.split(",").map((e) => e.trim().toLowerCase())
  : [];

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [

    GitHub({
      clientId: process.env.AUTH_GITHUB_ID || "mock_id",
      clientSecret: process.env.AUTH_GITHUB_SECRET || "mock_secret",
    }),
  ],
  pages: {
    signIn: "/auth/signin",
    error: "/auth/signin", // Redirect to sign-in page to display errors (handles 'Configuration')
  },
  callbacks: {
    async signIn({ user }) {
      if (allowedEmails.length === 0) return true;
      const email = user.email?.toLowerCase() || "";
      return allowedEmails.includes(email);
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub || "";
      }
      return session;
    },
    async jwt({ token, user }) {
      if (user) {
        token.email = user.email;
      }
      return token;
    },
  },
  session: {
    strategy: "jwt",
  },
});

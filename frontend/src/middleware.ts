export { auth as middleware } from "@/../../auth";

export const config = {
  matcher: [
    // Protect all routes except auth, api, static assets
    "/((?!auth|api|_next/static|_next/image|favicon.ico).*)",
  ],
};

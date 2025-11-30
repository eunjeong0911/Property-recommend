import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

console.log("GOOGLE_CLIENT_ID:", process.env.GOOGLE_CLIENT_ID ? "Loaded" : "Missing");
console.log("GOOGLE_CLIENT_SECRET:", process.env.GOOGLE_CLIENT_SECRET ? "Loaded" : "Missing");

const handler = NextAuth({
    providers: [
        GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID ?? "",
            clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
        }),
    ],
    callbacks: {
        async signIn({ user, account, profile }) {
            if (account?.provider === "google") {
                try {
                    // TODO: Replace with actual Django Backend API call
                    // const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/google/`, {
                    //   email: user.email,
                    //   name: user.name,
                    //   image: user.image,
                    //   googleId: account.providerAccountId,
                    // });

                    // Mock logic for demonstration:
                    // If it's a new user (simulated), mark as new and survey not completed
                    // In real app, response.data would contain this info
                    user.isNewUser = true; // Default to true for testing flow
                    user.surveyCompleted = false;

                    if (user.isNewUser && !user.surveyCompleted) {
                        return '/preferenceSurvey';
                    }

                    return true;
                } catch (error) {
                    console.error("Login failed:", error);
                    return false;
                }
            }
            return true;
        },
        async jwt({ token, user }) {
            // Initial sign in
            if (user) {
                token.isNewUser = user.isNewUser;
                token.surveyCompleted = user.surveyCompleted;
            }
            return token;
        },
        async session({ session, token }) {
            if (session.user) {
                session.user.isNewUser = token.isNewUser as boolean;
                session.user.surveyCompleted = token.surveyCompleted as boolean;
            }
            return session;
        },
    },
    pages: {
        signIn: '/login',
    }
});

export { handler as GET, handler as POST };

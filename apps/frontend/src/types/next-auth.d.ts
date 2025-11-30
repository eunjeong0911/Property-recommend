import NextAuth, { DefaultSession } from "next-auth";
import { JWT } from "next-auth/jwt";

declare module "next-auth" {
    interface Session {
        user: {
            id: string;
            isNewUser: boolean;
            surveyCompleted: boolean;
        } & DefaultSession["user"];
    }

    interface User {
        isNewUser?: boolean;
        surveyCompleted?: boolean;
    }
}

declare module "next-auth/jwt" {
    interface JWT {
        isNewUser?: boolean;
        surveyCompleted?: boolean;
    }
}

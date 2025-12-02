import NextAuth, { DefaultSession } from "next-auth";
import { JWT } from "next-auth/jwt";

declare module "next-auth" {
    interface Session {
        user: {
            id: string;
            userId?: number;
            isNewUser: boolean;
            surveyCompleted: boolean;
            accessToken?: string;
            refreshToken?: string;
        } & DefaultSession["user"];
    }

    interface User {
        isNewUser?: boolean;
        surveyCompleted?: boolean;
        accessToken?: string;
        refreshToken?: string;
        userId?: number;
    }
}

declare module "next-auth/jwt" {
    interface JWT {
        isNewUser?: boolean;
        surveyCompleted?: boolean;
        accessToken?: string;
        refreshToken?: string;
        userId?: number;
    }
}

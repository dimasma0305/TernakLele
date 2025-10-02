FROM node:20-slim AS front-base
COPY front /app
WORKDIR /app

FROM front-base as front-build
RUN npm install
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ARG NODE_ENV
ENV NODE_ENV=$NODE_ENV
RUN npm run build

FROM front-base
COPY --from=front-build /app/node_modules ./node_modules
COPY --from=front-build /app/.next/ ./.next
CMD ["npm", "run", "start"]

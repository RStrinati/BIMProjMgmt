# Revizto .NET Service Dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:6.0
WORKDIR /app
COPY . .
EXPOSE 5000
ENTRYPOINT ["dotnet", "ReviztoService.dll"]
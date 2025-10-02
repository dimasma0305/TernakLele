export function Footer() {
  return (
    <footer className="border-t">
      <div className="container flex h-14 items-center justify-between px-4 text-sm text-muted-foreground">
        <div>Ternak Lele © {new Date().getFullYear()}</div>
        <div>@dimasc.tf</div>
      </div>
    </footer>
  )
}

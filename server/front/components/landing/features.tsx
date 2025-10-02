import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Zap, Users, BarChart3 } from "lucide-react"

const features = [
  {
    icon: Zap,
    title: "Lightning-fast workflows",
    description:
      "Automate repetitive tasks and streamline your processes. Set up custom workflows that adapt to your team's unique needs and save hours every week.",
  },
  {
    icon: Users,
    title: "Real-time collaboration",
    description:
      "Work together seamlessly with your team. Share updates, assign tasks, and communicate in context. Everyone stays aligned without endless meetings.",
  },
  {
    icon: BarChart3,
    title: "Powerful insights",
    description:
      "Make data-driven decisions with comprehensive analytics. Track progress, identify bottlenecks, and optimize your team's performance with actionable insights.",
  },
]

export function Features() {
  return (
    <section className="py-20 md:py-32 bg-secondary/30">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-balance mb-4">
            Everything you need to succeed
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            Powerful features designed to help your team work smarter, not harder
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <Card key={index} className="border-border bg-card hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base leading-relaxed">{feature.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}

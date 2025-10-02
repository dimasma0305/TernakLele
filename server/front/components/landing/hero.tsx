import { Button } from "@/components/ui/button"
import { ArrowRight, CheckCircle2 } from "lucide-react"

export function Hero() {
  return (
    <section className="relative py-20 md:py-32 lg:py-40 overflow-hidden">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex flex-col items-center text-center gap-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary text-secondary-foreground text-sm font-medium">
            <CheckCircle2 className="h-4 w-4 text-primary" />
            <span>Trusted by 10,000+ teams worldwide</span>
          </div>

          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-balance max-w-5xl">
            Project management that <span className="text-primary">actually works</span>
          </h1>

          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl text-pretty leading-relaxed">
            TaskFlow helps teams collaborate seamlessly, track progress effortlessly, and deliver projects on time. Stop
            juggling tools and start flowing.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 mt-4">
            <Button size="lg" className="text-base px-8 h-12 font-semibold">
              Start free trial
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button size="lg" variant="outline" className="text-base px-8 h-12 font-semibold bg-transparent">
              Watch demo
            </Button>
          </div>

          <div className="flex items-center gap-6 mt-8 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              <span>14-day free trial</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              <span>Cancel anytime</span>
            </div>
          </div>
        </div>

        {/* Hero Image Placeholder */}
        <div className="mt-16 md:mt-24">
          <div className="relative rounded-xl overflow-hidden border border-border shadow-2xl bg-card">
            <img src="/placeholder.svg?height=600&width=1200" alt="TaskFlow Dashboard" className="w-full h-auto" />
          </div>
        </div>
      </div>
    </section>
  )
}

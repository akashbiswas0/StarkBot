import { BenefitsSection } from "@/components/layout/sections/benefits";
import { FAQSection } from "@/components/layout/sections/faq";
import { FeaturesSection } from "@/components/layout/sections/features";
import { HeroSection } from "@/components/layout/sections/hero";

import { ServicesSection } from "@/components/layout/sections/services";


export default function Home() {
  return (
    <>
      <HeroSection />
      
      <BenefitsSection />
      <FeaturesSection />
      <ServicesSection />
      
     
      <FAQSection />
    </>
  );
}
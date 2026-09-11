/**
 * LumicorePro — Local Image Registry
 * All images are stored in src/assets/images/ and served from the Vite build.
 * Run `node scripts/download-images.mjs` to refresh local images.
 */

/* ── Vite static imports — bundled & hashed ──────────────────────── */
// Restaurant
import restHero from '@/assets/images/restaurant/hero.jpg';
import restDish1 from '@/assets/images/restaurant/dish1.jpg';
import restDish2 from '@/assets/images/restaurant/dish2.jpg';
import restDish3 from '@/assets/images/restaurant/dish3.jpg';
import restDish4 from '@/assets/images/restaurant/dish4.jpg';
import restDish5 from '@/assets/images/restaurant/dish5.jpg';
import restDish6 from '@/assets/images/restaurant/dish6.jpg';
import restInterior from '@/assets/images/restaurant/interior.jpg';
import restChef from '@/assets/images/restaurant/chef.jpg';
// Real Estate
import reHero from '@/assets/images/realestate/hero.jpg';
import reProp1 from '@/assets/images/realestate/prop1.jpg';
import reProp2 from '@/assets/images/realestate/prop2.jpg';
import reProp3 from '@/assets/images/realestate/prop3.jpg';
import reProp4 from '@/assets/images/realestate/prop4.jpg';
import reProp5 from '@/assets/images/realestate/prop5.jpg';
import reInterior from '@/assets/images/realestate/interior.jpg';
import reAgent from '@/assets/images/realestate/agent.jpg';
// Healthcare
import hcHero from '@/assets/images/healthcare/hero.jpg';
import hcDoc1 from '@/assets/images/healthcare/doctor1.jpg';
import hcDoc2 from '@/assets/images/healthcare/doctor2.jpg';
import hcDoc3 from '@/assets/images/healthcare/doctor3.jpg';
import hcDoc4 from '@/assets/images/healthcare/doctor4.jpg';
import hcDoc5 from '@/assets/images/healthcare/doctor5.jpg';
import hcHospital from '@/assets/images/healthcare/hospital.jpg';
// Fitness
import fitHero from '@/assets/images/fitness/hero.jpg';
import fitGym1 from '@/assets/images/fitness/gym1.jpg';
import fitGym2 from '@/assets/images/fitness/gym2.jpg';
import fitTrainer1 from '@/assets/images/fitness/trainer1.jpg';
import fitTrainer2 from '@/assets/images/fitness/trainer2.jpg';
import fitTrainer3 from '@/assets/images/fitness/trainer3.jpg';
import fitTrainer4 from '@/assets/images/fitness/trainer4.jpg';
import fitClass1 from '@/assets/images/fitness/class1.jpg';
import fitClass2 from '@/assets/images/fitness/class2.jpg';
// Education
import eduHero from '@/assets/images/education/hero.jpg';
import eduCourse1 from '@/assets/images/education/course1.jpg';
import eduCourse2 from '@/assets/images/education/course2.jpg';
import eduCourse3 from '@/assets/images/education/course3.jpg';
import eduCourse4 from '@/assets/images/education/course4.jpg';
import eduCourse5 from '@/assets/images/education/course5.jpg';
import eduCourse6 from '@/assets/images/education/course6.jpg';
import eduStudent from '@/assets/images/education/student.jpg';
// Travel
import travHero from '@/assets/images/travel/hero.jpg';
import travDest1 from '@/assets/images/travel/dest1.jpg';
import travDest2 from '@/assets/images/travel/dest2.jpg';
import travDest3 from '@/assets/images/travel/dest3.jpg';
import travDest4 from '@/assets/images/travel/dest4.jpg';
import travDest5 from '@/assets/images/travel/dest5.jpg';
import travDest6 from '@/assets/images/travel/dest6.jpg';
import travPlane from '@/assets/images/travel/plane.jpg';
// Portfolio
import portHero from '@/assets/images/portfolio/hero.jpg';
import portAvatar from '@/assets/images/portfolio/avatar.jpg';
import portProject1 from '@/assets/images/portfolio/project1.jpg';
import portProject2 from '@/assets/images/portfolio/project2.jpg';
import portProject3 from '@/assets/images/portfolio/project3.jpg';
import portWorkspace from '@/assets/images/portfolio/workspace.jpg';
import portCode from '@/assets/images/portfolio/code.jpg';
// Creative
import crHero from '@/assets/images/creative/hero.jpg';
import crProj1 from '@/assets/images/creative/project1.jpg';
import crProj2 from '@/assets/images/creative/project2.jpg';
import crProj3 from '@/assets/images/creative/project3.jpg';
import crProj4 from '@/assets/images/creative/project4.jpg';
import crTeam1 from '@/assets/images/creative/team1.jpg';
import crTeam2 from '@/assets/images/creative/team2.jpg';
import crTeam3 from '@/assets/images/creative/team3.jpg';
import crTeam4 from '@/assets/images/creative/team4.jpg';
// E-Commerce
import ecHero from '@/assets/images/ecommerce/hero.jpg';
import ecProd1 from '@/assets/images/ecommerce/product1.jpg';
import ecProd2 from '@/assets/images/ecommerce/product2.jpg';
import ecProd3 from '@/assets/images/ecommerce/product3.jpg';
import ecProd4 from '@/assets/images/ecommerce/product4.jpg';
import ecProd5 from '@/assets/images/ecommerce/product5.jpg';
import ecProd6 from '@/assets/images/ecommerce/product6.jpg';
import ecProd7 from '@/assets/images/ecommerce/product7.jpg';
import ecProd8 from '@/assets/images/ecommerce/product8.jpg';
// Business
import bizHero from '@/assets/images/business/hero.jpg';
import bizTeam from '@/assets/images/business/team.jpg';
import bizOffice from '@/assets/images/business/office.jpg';
import bizMeeting from '@/assets/images/business/meeting.jpg';
import bizCity from '@/assets/images/business/city.jpg';
import bizGrowth from '@/assets/images/business/growth.jpg';
// AI
import aiHero from '@/assets/images/ai/hero.jpg';
import aiChip from '@/assets/images/ai/chip.jpg';
import aiCode from '@/assets/images/ai/code.jpg';
import aiRobot from '@/assets/images/ai/robot.jpg';
import aiData from '@/assets/images/ai/data.jpg';
// Dashboard
import dbHero from '@/assets/images/dashboard/hero.jpg';
import dbAnalytics from '@/assets/images/dashboard/analytics.jpg';
import dbUser1 from '@/assets/images/dashboard/user1.jpg';
import dbUser2 from '@/assets/images/dashboard/user2.jpg';
import dbUser3 from '@/assets/images/dashboard/user3.jpg';

/* ── Structured image map ─────────────────────────────────────────── */
export const img = {
  restaurant: {
    hero: restHero,
    dish1: restDish1,
    dish2: restDish2,
    dish3: restDish3,
    dish4: restDish4,
    dish5: restDish5,
    dish6: restDish6,
    interior: restInterior,
    chef: restChef,
  },
  realestate: {
    hero: reHero,
    prop1: reProp1,
    prop2: reProp2,
    prop3: reProp3,
    prop4: reProp4,
    prop5: reProp5,
    interior: reInterior,
    agent: reAgent,
  },
  healthcare: {
    hero: hcHero,
    doctor1: hcDoc1,
    doctor2: hcDoc2,
    doctor3: hcDoc3,
    doctor4: hcDoc4,
    doctor5: hcDoc5,
    hospital: hcHospital,
  },
  fitness: {
    hero: fitHero,
    gym1: fitGym1,
    gym2: fitGym2,
    trainer1: fitTrainer1,
    trainer2: fitTrainer2,
    trainer3: fitTrainer3,
    trainer4: fitTrainer4,
    class1: fitClass1,
    class2: fitClass2,
  },
  education: {
    hero: eduHero,
    course1: eduCourse1,
    course2: eduCourse2,
    course3: eduCourse3,
    course4: eduCourse4,
    course5: eduCourse5,
    course6: eduCourse6,
    student: eduStudent,
  },
  travel: {
    hero: travHero,
    dest1: travDest1,
    dest2: travDest2,
    dest3: travDest3,
    dest4: travDest4,
    dest5: travDest5,
    dest6: travDest6,
    plane: travPlane,
  },
  portfolio: {
    hero: portHero,
    avatar: portAvatar,
    project1: portProject1,
    project2: portProject2,
    project3: portProject3,
    workspace: portWorkspace,
    code: portCode,
  },
  creative: {
    hero: crHero,
    project1: crProj1,
    project2: crProj2,
    project3: crProj3,
    project4: crProj4,
    team1: crTeam1,
    team2: crTeam2,
    team3: crTeam3,
    team4: crTeam4,
  },
  ecommerce: {
    hero: ecHero,
    product1: ecProd1,
    product2: ecProd2,
    product3: ecProd3,
    product4: ecProd4,
    product5: ecProd5,
    product6: ecProd6,
    product7: ecProd7,
    product8: ecProd8,
  },
  business: {
    hero: bizHero,
    team: bizTeam,
    office: bizOffice,
    meeting: bizMeeting,
    city: bizCity,
    growth: bizGrowth,
  },
  ai: { hero: aiHero, chip: aiChip, code: aiCode, robot: aiRobot, data: aiData },
  dashboard: {
    hero: dbHero,
    analytics: dbAnalytics,
    user1: dbUser1,
    user2: dbUser2,
    user3: dbUser3,
  },
  people: {
    male1: portAvatar,
    male2: crTeam1,
    male3: crTeam3,
    female1: crTeam2,
    female2: crTeam4,
    female3: hcDoc5,
  },
};

export default img;

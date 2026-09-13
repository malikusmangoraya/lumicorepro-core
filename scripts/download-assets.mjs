/**
 * LumicorePro — Full Asset Downloader (v2)
 * Downloads 20+ curated Unsplash images per category into src/assets/images/
 * Verified as real JPEGs (magic bytes + min size), deduped across targets.
 * Run: node scripts/download-assets.mjs [--topup]
 */
import https from 'https';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');
const TARGET = 20;

// Pool per category folder. Each entry: [unsplashId, width, height, relPath]
const POOLS = {
  business: [
    ['1556761175-5973dc0f32e7', 900, 500, 'business/work-meeting1.jpg'],
    ['1556761175-b413da4baf72', 900, 500, 'business/work-meeting2.jpg'],
    ['1552664730-d307ca884978', 900, 500, 'business/strategy.jpg'],
    ['1573497019940-1c28c88b4f3e', 400, 500, 'business/professional-female.jpg'],
    ['1573496359142-b8d87734a5a2', 400, 500, 'business/professional-male.jpg'],
    ['1519085360753-af0119f7cbe7', 400, 500, 'business/executive.jpg'],
    ['1502323777039-f29e397f2c47', 400, 500, 'business/presentation.jpg'],
    ['1521737604893-d14cc237f11d', 900, 500, 'business/brainstorm.jpg'],
    ['1554409134-7ba3c7e36afe', 900, 500, 'business/summit.jpg'],
    ['1486406146926-c627a92ad1ab', 900, 500, 'business/building-modern.jpg'],
    ['1507679799987-c73779587ccf', 900, 500, 'business/corporate-space.jpg'],
    ['1497215842964-222b430dc094', 900, 500, 'business/office-desk.jpg'],
    ['1504384308090-c894fdcc538d', 900, 500, 'business/focus-work.jpg'],
    ['1499951360447-b19be8fe80f5', 900, 500, 'business/laptop-setup.jpg'],
    ['1497366216548-37526070297c', 1200, 500, 'business/hero-desk.jpg'],
    ['1542744173-8e7e53415bb0', 900, 500, 'business/analytics-deck.jpg'],
    ['1526304640581-d334cdbbf45e', 900, 500, 'business/finance.jpg'],
    ['1579621970563-ebec7560ff3e', 900, 500, 'business/wealth.jpg'],
    ['1563013544-824ae1b704d3', 900, 500, 'business/cards.jpg'],
    ['1551288049-bebda4e38f71', 900, 500, 'business/growth-chart.jpg'],
    ['1444653614673-5d6c4b1e9611', 900, 500, 'business/analytics-board.jpg'],
    ['1450101499163-c8848c66ca85', 900, 500, 'business/handshake-deal.jpg'],
    ['1507679799987-c73779587ccf', 900, 500, 'business/space-alt.jpg'],
    ['1462392246754-28b127cd76d4', 900, 500, 'business/waterfall.jpg'],
  ],
  ai: [
    ['1518770660439-4636190af475', 1200, 500, 'ai/hero-chip.jpg'],
    ['1531297484001-80022131f5a1', 900, 500, 'ai/code-dark.jpg'],
    ['1555066931-4365d14bab8c', 900, 500, 'ai/code-screen.jpg'],
    ['1555949963-aa79dcee981c', 900, 500, 'ai/neural-light.jpg'],
    ['1558494949-ef010cbdcc31', 900, 500, 'ai/chip-focus.jpg'],
    ['1485827404703-89b55fcc595e', 900, 500, 'ai/robot.jpg'],
    ['1526374965328-7f61d4dc18c5', 900, 500, 'ai/tech-glitch.jpg'],
    ['1483817101829-339b08e8d583', 900, 500, 'ai/interconnect.jpg'],
    ['1451187580459-43490279c0fa', 1200, 500, 'ai/earth-data.jpg'],
    ['1523961131990-5ea7c6b21087', 900, 500, 'ai/data-flow.jpg'],
    ['1504868584819-f8e8b4b6d7e3', 900, 500, 'ai/design-tools.jpg'],
    ['1550751827-4bd374c3f58b', 900, 500, 'ai/security.jpg'],
    ['1504639725590-34d0984388bd', 900, 500, 'ai/brain-lines.jpg'],
    ['1550745165-9bc0b252726f', 900, 500, 'ai/game-tech.jpg'],
    ['1515879218367-8466d910aaa4', 900, 500, 'ai/bitcoin.jpg'],
    ['1487889718321-5ca1d46d2652', 900, 500, 'ai/robot-arm.jpg'],
    ['1531746020798-e6953c6e8e04', 900, 500, 'ai/coffee-focus.jpg'],
    ['1516321318423-f06f85e504b3', 900, 500, 'ai/knowledge.jpg'],
    ['1519389950473-47ba0277781c', 900, 500, 'ai/team-tech.jpg'],
    ['1522205408450-114d54d2a4a6', 900, 500, 'ai/workspace-laptop.jpg'],
    ['1472289065587-832e6808d765', 900, 500, 'ai/brain-storm.jpg'],
    ['1550751827-4bd374c3f58b', 900, 500, 'ai/cyber.jpg'],
  ],
  creative: [
    ['1558655146-9f40138edfeb', 1200, 500, 'creative/hero-art.jpg'],
    ['1561070791-2526d30994b5', 700, 500, 'creative/design-desktop.jpg'],
    ['1573167243872-43c6433b9d40', 700, 500, 'creative/branding.jpg'],
    ['1529336953128-a85760f58ea1', 700, 500, 'creative/camera-work.jpg'],
    ['1541701494-16e8d485b12c', 700, 500, 'creative/painting.jpg'],
    ['1470252649378-9c29740c9fa8', 700, 500, 'creative/studio-desk.jpg'],
    ['1561729023-2f2f7acc3a95', 700, 500, 'creative/color-palette.jpg'],
    ['1497032628192-86f99bcd76bc', 700, 500, 'creative/notebook-pen.jpg'],
    ['1497366242310-1cfb1165af64', 700, 500, 'creative/brainstorm.jpg'],
    ['1547891654-e66ed7ebb968', 700, 500, 'creative/design-pattern.jpg'],
    ['1558655146-9f40138edfeb', 700, 500, 'creative/gallery.jpg'],
    ['1507235098691-a4183cea3b17', 700, 500, 'creative/swatches.jpg'],
    ['1452807332-6f7b4b2e5a26', 700, 500, 'creative/creative-mind.jpg'],
    ['1521590832167-7bcbfaa6381f', 700, 500, 'creative/colorful-space.jpg'],
    ['1548681528-6a5c1b4c9af8', 700, 500, 'creative/palette.jpg'],
    ['1525340115178-ad59ae4791f5', 700, 500, 'creative/design-table.jpg'],
    ['1531835413629-7412538ede74', 700, 500, 'creative/workstation.jpg'],
    ['1499951360447-b19be8fe80f5', 700, 500, 'creative/laptop-air.jpg'],
    ['1521572163474-6864f9cf17ab', 700, 500, 'creative/lookbook.jpg'],
    ['1512453979798-5ea266f8880c', 700, 500, 'creative/moodboard.jpg'],
  ],
  dashboard: [
    ['1551288049-bebda4e38f71', 1200, 500, 'dashboard/hero-kpis.jpg'],
    ['1460925895917-afdab827c52f', 900, 500, 'dashboard/analytics-laptop.jpg'],
    ['1553877522-43269d4ea984', 900, 500, 'dashboard/desk-dashboard.jpg'],
    ['1543286385-121b60d21f18', 900, 500, 'dashboard/data-screen.jpg'],
    ['1550751827-4bd374c3f58b', 900, 500, 'dashboard/security-dash.jpg'],
    ['1498050108023-c5249f4df085', 900, 500, 'dashboard/code-dash.jpg'],
    ['1519241047957-b31eb8f1b56b', 900, 500, 'dashboard/blueprint.jpg'],
    ['1526392060635-9d601a43700c', 900, 500, 'dashboard/circuit-dash.jpg'],
    ['1556742049-0cfed4f6a45d', 900, 500, 'dashboard/payments-dash.jpg'],
    ['1559526324-4b87b5e36e44', 900, 500, 'dashboard/analytics-phone.jpg'],
    ['1551434678-e076c223a692', 1600, 900, 'dashboard/code-editor.jpg'],
    ['1467232004584-a241de8bcf5d', 900, 500, 'dashboard/chart-notes.jpg'],
    ['1504868344812-e8c9c2a98e78', 900, 500, 'dashboard/planning.jpg'],
    ['1522205408450-114d54d2a4a6', 900, 500, 'dashboard/study-dash.jpg'],
    ['1531297484001-80022131f5a1', 900, 500, 'dashboard/terminal.jpg'],
    ['1504384308090-c894fdcc538d', 900, 500, 'dashboard/focus-dash.jpg'],
  ],
  education: [
    ['1523050854058-8df90110c9f1', 1200, 500, 'education/hero-grad.jpg'],
    ['1516321318423-f06f85e504b3', 600, 380, 'education/book-write.jpg'],
    ['1488190211105-8b0e65b80b4e', 600, 380, 'education/notes.jpg'],
    ['1509062522246-3b57f9e6b4c4', 600, 380, 'education/board-math.jpg'],
    ['1558021212-51b6ecfa0db9', 600, 380, 'education/kids-labs.jpg'],
    ['1456513080510-7bf3a84b82f8', 600, 380, 'education/hand-write.jpg'],
    ['1434030216411-0b5e530e1b08', 600, 380, 'education/kid-study.jpg'],
    ['1523240795612-9a054b0db644', 900, 500, 'education/campus.jpg'],
    ['1522205408450-114d54d2a4a6', 600, 380, 'education/laptop-course.jpg'],
    ['1503676260728-1c00da094a0b', 600, 380, 'education/study-desk.jpg'],
    ['1481627834876-b7833e8f5b3', 600, 380, 'education/open-books.jpg'],
    ['1478063722078-5784298c48d7', 900, 500, 'education/students.jpg'],
    ['1580894732444-8ecdad790a17', 600, 380, 'education/microscope.jpg'],
    ['1532094349884-543bc11b234d', 600, 380, 'education/lab-vials.jpg'],
    ['1523580494863-6f3031224c94', 900, 500, 'education/university.jpg'],
    ['1519452635265-7b07f31d7c14', 600, 380, 'education/online-class.jpg'],
    ['1454165804606-c3d57bc86b40', 600, 380, 'education/planning-clipboard.jpg'],
    ['1427504494785-3a9ca7044f45', 900, 500, 'education/classroom.jpg'],
    ['1544717305-2782c9b6b350', 900, 500, 'education/teacher.jpg'],
    ['1503614472-8c93d56e92ce', 900, 500, 'education/child-computer.jpg'],
  ],
  ecommerce: [
    ['1523275335684-37898b6baf30', 500, 500, 'ecommerce/product-watch.jpg'],
    ['1542291026-7eec264c27ff', 500, 500, 'ecommerce/product-sneaker.jpg'],
    ['1553454377-3411fe5a1e62', 500, 500, 'ecommerce/product-headphones.jpg'],
    ['1583394838336-acd977736f90', 500, 500, 'ecommerce/product-keyboard.jpg'],
    ['1526170375885-4d8ecf77b99f', 500, 500, 'ecommerce/product-camera.jpg'],
    ['1572635196237-14b3f281503f', 500, 500, 'ecommerce/product-sunglasses.jpg'],
    ['1519052537078-e6302a4968d4', 900, 500, 'ecommerce/shopping-bags.jpg'],
    ['1441986300917-64674bd600d8', 900, 500, 'ecommerce/clothing-rack.jpg'],
    ['1483985988355-76b729e93aa8', 900, 500, 'ecommerce/fashion-model.jpg'],
    ['1490481651871-ab68de247627', 900, 500, 'ecommerce/fashion-look.jpg'],
    ['1487222477894-8943e31ef7b2', 900, 500, 'ecommerce/denim-rack.jpg'],
    ['1537838155917-b0e4f9e3b7df', 900, 500, 'ecommerce/accessories.jpg'],
    ['1491637639811-60e2756cc1c7', 900, 500, 'ecommerce/cosmetics.jpg'],
    ['1521590832167-7bcbfaa6381f', 900, 500, 'ecommerce/colorful-bags.jpg'],
    ['1485969368732-b08989198517', 900, 500, 'ecommerce/envelope.jpg'],
    ['1505740420928-5e4135fd5317', 900, 500, 'ecommerce/watch-glass.jpg'],
    ['1523275335684-37898b6baf30', 500, 500, 'ecommerce/product-smartwatch.jpg'],
    ['1596462502272-27bf8c0ae9ae', 500, 500, 'ecommerce/product-bottle.jpg'],
    ['1560806887-1e4cd0b6cbd6', 500, 500, 'ecommerce/product-sneaker2.jpg'],
    ['1549298916-b41d501d3772', 500, 500, 'ecommerce/product-shoe.jpg'],
  ],
  'ecommerce/electronics': [
    ['1511707171634-5f897ff02aa9', 500, 500, 'ecommerce/electronics/phone.jpg'],
    ['1496181133206-80ce9b88a853', 500, 500, 'ecommerce/electronics/laptop.jpg'],
    ['1523275335684-37898b6baf30', 500, 500, 'ecommerce/electronics/smartwatch.jpg'],
    ['1542291026-7eec264c27ff', 500, 500, 'ecommerce/electronics/sneaker.jpg'],
    ['1583394838336-acd977736f90', 500, 500, 'ecommerce/electronics/keyboard.jpg'],
    ['1546868871-7041f2a55e12', 500, 500, 'ecommerce/electronics/fitness-band.jpg'],
    ['1553454377-3411fe5a1e62', 500, 500, 'ecommerce/electronics/headset.jpg'],
    ['1526170375885-4d8ecf77b99f', 500, 500, 'ecommerce/electronics/camera.jpg'],
    ['1495121606077-2c4e8a0b6f5a', 500, 500, 'ecommerce/electronics/tv.jpg'],
    ['1496181133206-80ce9b88a853', 500, 500, 'ecommerce/electronics/ultrabook.jpg'],
    ['1521490894742-4891bd35b9f9', 500, 500, 'ecommerce/electronics/gadget.jpg'],
    ['1533227268428-f9ed0900fb3b', 500, 500, 'ecommerce/electronics/gaming.jpg'],
    ['1550745165-9bc0b252726f', 500, 500, 'ecommerce/electronics/retro-console.jpg'],
    ['1520551303764-b40b4dd8e00c', 500, 500, 'ecommerce/electronics/drone.jpg'],
    ['1546877625-cb8c71916308', 500, 500, 'ecommerce/electronics/tablet.jpg'],
    ['1545239351-ef35f43d514b', 500, 500, 'ecommerce/electronics/earbuds.jpg'],
    ['1526406915892-158314e1ec9c', 500, 500, 'ecommerce/electronics/speaker.jpg'],
    ['1550009158-9ebf69173e03', 500, 500, 'ecommerce/electronics/vr-headset.jpg'],
    ['1535223289827-42f8eeb3153a', 500, 500, 'ecommerce/electronics/phone-dock.jpg'],
    ['1526738544334-6b6108f2e7c5', 500, 500, 'ecommerce/electronics/server.jpg'],
  ],
  fitness: [
    ['1534438327276-14e5300c3a48', 1200, 500, 'fitness/hero-gym.jpg'],
    ['1571019613454-1cb2f99b2d8b', 600, 400, 'fitness/weights.jpg'],
    ['1517836357463-d25dfeac3438', 600, 400, 'fitness/kettlebell.jpg'],
    ['1548690312-855d4bfaa66a', 400, 500, 'fitness/coach.jpg'],
    ['1549476464-37392f717d84', 400, 500, 'fitness/trainer.jpg'],
    ['1552674605-db5fecabfe68', 400, 500, 'fitness/boxing.jpg'],
    ['1518611012118-696072aa579a', 600, 400, 'fitness/class.jpg'],
    ['1544367567-0f2fcb009e0b', 600, 400, 'fitness/yoga-class.jpg'],
    ['1526506118085-60ce8714f8c5', 600, 400, 'fitness/running.jpg'],
    ['1567597261545-c588d7f5f24d', 600, 400, 'fitness/yoga-pose.jpg'],
    ['1550990195-e2fe781c0d68', 600, 400, 'fitness/healthy-diet.jpg'],
    ['1518459031867-89531141e44b', 600, 400, 'fitness/bands.jpg'],
    ['1534251369789-5067c8b8602a', 600, 400, 'fitness/crossfit.jpg'],
    ['1571731956672-8b32223a7a4d', 600, 400, 'fitness/strength.jpg'],
    ['1517963879433-6ad2b056d712', 600, 400, 'fitness/dumbbells.jpg'],
    ['1605296867304-46d5465a13f1', 600, 400, 'fitness/hiit.jpg'],
    ['1594737625785-a26c78a4557f', 600, 400, 'fitness/woman-gym.jpg'],
    ['1583454110551-21f2fa2afe61', 600, 400, 'fitness/woman-exercise.jpg'],
    ['1549060279-7e168fcee0c2', 600, 400, 'fitness/jump.jpg'],
    ['1543373014-c2c9ee8064b8', 600, 400, 'fitness/sprints.jpg'],
  ],
  healthcare: [
    ['1576091160550-2173dba999ef', 1200, 500, 'healthcare/hero-doctor.jpg'],
    ['1612349317150-e413f6a5b16d', 400, 400, 'healthcare/doc-male.jpg'],
    ['1559839734-2b71ea197ec2', 400, 400, 'healthcare/doc-female.jpg'],
    ['1582750433449-648ed127bb54', 400, 400, 'healthcare/doc-consult.jpg'],
    ['1594824476967-48c8b964273f', 400, 400, 'healthcare/doc-tablet.jpg'],
    ['1527613426441-4da17471b66d', 400, 400, 'healthcare/doc-clipboard.jpg'],
    ['1519494026892-80bbd2d6fd0d', 800, 400, 'healthcare/hospital-build.jpg'],
    ['1538108149393-fbbd81895907', 800, 400, 'healthcare/hospital-hall.jpg'],
    ['1576669801831-6791d8c05b6e', 800, 400, 'healthcare/shield-care.jpg'],
    ['1631217868264-e5b90bb7e133', 800, 400, 'healthcare/telehealth.jpg'],
    ['1583912267550-044b5ed2971a', 800, 400, 'healthcare/video-consult.jpg'],
    ['1530026186672-2cd00ffc50fe', 400, 400, 'healthcare/nurse.jpg'],
    ['1584987648055-7d48d0831e19', 600, 400, 'healthcare/lab-test.jpg'],
    ['1587825140708-dfaf72ae4b04', 600, 400, 'healthcare/vials.jpg'],
    ['1505751172876-fa1923c5c528', 600, 400, 'healthcare/pharmacy.jpg'],
    ['1584634731339-252c581d43e5', 600, 400, 'healthcare/dental.jpg'],
    ['1588776814546-daab30f310ce', 600, 400, 'healthcare/lab-tech.jpg'],
    ['1532938911079-1b06ac7ceec7', 600, 400, 'healthcare/med-tech.jpg'],
    ['1571772996211-2f02c9727629', 600, 400, 'healthcare/med-kit.jpg'],
    ['1562436568-9b0e1860175b', 600, 400, 'healthcare/diagnostics.jpg'],
  ],
  portfolio: [
    ['1498050108023-c5249f4df085', 1200, 500, 'portfolio/hero-code.jpg'],
    ['1461749280684-dccba630e2f6', 700, 450, 'portfolio/dev-code.jpg'],
    ['1467232004584-a241de8bcf5d', 700, 450, 'portfolio/mockups.jpg'],
    ['1504868584819-f8e8b4b6d7e3', 700, 450, 'portfolio/ui-design.jpg'],
    ['1486312338219-ce68d2c6f44d', 900, 500, 'portfolio/workspace-desk.jpg'],
    ['1555066931-4365d14bab8c', 700, 400, 'portfolio/terminal.jpg'],
    ['1531538606174-0f90ff5dce83', 700, 450, 'portfolio/resume.jpg'],
    ['1522653217964-44047726a14d', 700, 450, 'portfolio/editor.jpg'],
    ['1561070791-2526d30994b5', 700, 450, 'portfolio/brand-design.jpg'],
    ['1547658719-da2b51169166', 700, 450, 'portfolio/saas-design.jpg'],
    ['1531403009284-440f080d1e12', 700, 450, 'portfolio/designer-desk.jpg'],
    ['1529111290557-82f2dbd8a9d2', 700, 450, 'portfolio/team-collab.jpg'],
    ['1481487196290-c410272f6e51', 700, 450, 'portfolio/creative-coding.jpg'],
    ['1522327648973-38e079d99cca', 700, 450, 'portfolio/sketch.jpg'],
    ['1517180102446-f3ece451e9d8', 700, 450, 'portfolio/mb-work.jpg'],
    ['1512486130939-2c4f79935e4f', 700, 450, 'portfolio/phone-dev.jpg'],
    ['1533227268428-f9ed0900fb3b', 700, 450, 'portfolio/gaming-dev.jpg'],
    ['1558655146-9f40138edfeb', 700, 450, 'portfolio/art-print.jpg'],
  ],
  realestate: [
    ['1570129477492-45c003dc5c19', 1200, 500, 'realestate/hero-house.jpg'],
    ['1512917774080-9991f1c4c750', 600, 400, 'realestate/modern-home.jpg'],
    ['1600585154340-be6161a56a0c', 600, 400, 'realestate/luxury-villa.jpg'],
    ['1558618666-fcd25c85cd64', 600, 400, 'realestate/villa-front.jpg'],
    ['1564013799919-ab600027ffc6', 600, 400, 'realestate/living-room.jpg'],
    ['1523217582562-09d05ba57b90', 600, 400, 'realestate/bedroom.jpg'],
    ['1586023492125-27b2c045efd7', 800, 400, 'realestate/lounge.jpg'],
    ['1580587771525-78b9dba3b914', 600, 400, 'realestate/pool-house.jpg'],
    ['1500382017468-9049fed747ef', 600, 400, 'realestate/property.jpg'],
    ['1522708323590-d24dbb6b0267', 800, 400, 'realestate/apartment-living.jpg'],
    ['1493809842364-78817add7ffb', 800, 400, 'realestate/home-decor.jpg'],
    ['1600607687939-ce8a6c25118c', 800, 400, 'realestate/interior-lux.jpg'],
    ['1600607687920-4e2a09cf159d', 800, 400, 'realestate/chair-interior.jpg'],
    ['1556228453-efd6c1ff04f6', 600, 400, 'realestate/condo-view.jpg'],
    ['1568605114967-8130f3a36994', 600, 400, 'realestate/dusk-home.jpg'],
    ['1518780664697-55e3ad937233', 600, 400, 'realestate/twilight-home.jpg'],
    ['1448630360428-65456885c650', 600, 400, 'realestate/beach-house.jpg'],
    ['1470770841072-f978cf4d019e', 600, 400, 'realestate/cabin-lake.jpg'],
    ['1517021897933-0e0319cfbc28', 600, 400, 'realestate/arch-modern.jpg'],
    ['1524758631624-e2822e304c36', 600, 400, 'realestate/work-desk-home.jpg'],
  ],
  restaurant: [
    ['1414235135510-cd386a95cef3', 1200, 500, 'restaurant/hero-cooking.jpg'],
    ['1504674900247-0877df9cc836', 600, 400, 'restaurant/dish-veg.jpg'],
    ['1512621776951-a57141f2eefd', 600, 400, 'restaurant/salad-bowl.jpg'],
    ['1565299624946-b28f40a0ae38', 600, 400, 'restaurant/burger.jpg'],
    ['1546069901-ba9599a7e63c', 600, 400, 'restaurant/colorful-salad.jpg'],
    ['1567620905732-2d1ec7ab7445', 600, 400, 'restaurant/pancakes.jpg'],
    ['1555939594-58329b74c80a', 600, 400, 'restaurant/steak.jpg'],
    ['1504754524776-8f4f37790ca0', 600, 400, 'restaurant/meat-dish.jpg'],
    ['1559339352-11d035aa65de', 800, 400, 'restaurant/interior-tables.jpg'],
    ['1517248135467-4c7edcad34c4', 800, 400, 'restaurant/table-setup.jpg'],
    ['1466978913421-dad2ebd01d17', 800, 400, 'restaurant/lavish-dish.jpg'],
    ['1565958011703-44f9829ba187', 600, 400, 'restaurant/dessert.jpg'],
    ['1551024506-0bccd828d307', 600, 400, 'restaurant/choco-dessert.jpg'],
    ['1473093295043-cdd812d0e601', 600, 400, 'restaurant/pasta.jpg'],
    ['1482049016688-2d3e1b311543', 600, 400, 'restaurant/brunch.jpg'],
    ['1484723091739-30a097e8f929', 600, 400, 'restaurant/toast.jpg'],
    ['1559847844-5315695dadae', 600, 400, 'restaurant/chef-plating.jpg'],
    ['1507048331191-0d281e967e92', 600, 400, 'restaurant/flame-cook.jpg'],
    ['1556910103-1c02745aae4d', 600, 400, 'restaurant/kitchen-team.jpg'],
    ['1515003197210-e0cd71810b5f', 800, 400, 'restaurant/bar-tap.jpg'],
  ],
  saas: [
    ['1461749280684-dccba630e2f6', 1200, 500, 'saas/hero-code.jpg'],
    ['1551650975-87deedd944c3', 900, 500, 'saas/mobile-first.jpg'],
    ['1555774698-0e41e48a575c', 900, 500, 'saas/browser-app.jpg'],
    ['1522542550221-31fd19575a2d', 900, 500, 'saas/dev-desk.jpg'],
    ['1547658719-da2b51169166', 900, 500, 'saas/dashboard-ui.jpg'],
    ['1531297484001-80022131f5a1', 900, 500, 'saas/code-dark.jpg'],
    ['1519389950473-47ba0277781c', 900, 500, 'saas/team-devices.jpg'],
    ['1504868344812-e8c9c2a98e78', 900, 500, 'saas/productivity.jpg'],
    ['1551434678-e076c223a692', 900, 500, 'saas/editor-screen.jpg'],
    ['1522205408450-114d54d2a4a6', 900, 500, 'saas/focus-app.jpg'],
    ['1498050108023-c5249f4df085', 900, 500, 'saas/api-code.jpg'],
    ['1556742049-0cfed4f6a45d', 900, 500, 'saas/payments-app.jpg'],
    ['1559526324-4b87b5e36e44', 900, 500, 'saas/analytics-app.jpg'],
    ['1553877522-43269d4ea984', 900, 500, 'saas/desk-work.jpg'],
    ['1554409134-7ba3c7e36afe', 900, 500, 'saas/team-stack.jpg'],
    ['1550751827-4bd374c3f58b', 900, 500, 'saas/security-app.jpg'],
    ['1518438406772-77e912b79a3c', 900, 500, 'saas/startup-notes.jpg'],
    ['1556761175-5973dc0f32e7', 900, 500, 'saas/meeting-lap.jpg'],
    ['1521737604893-d14cc237f11d', 900, 500, 'saas/brainstorm-team.jpg'],
    ['1441984904996-e0b6ba687e04', 900, 500, 'saas/office-green.jpg'],
  ],
  fintech: [
    ['1563013544-824ae1b704d3', 1200, 500, 'fintech/hero-card.jpg'],
    ['1556742049-0cfed4f6a45d', 900, 500, 'fintech/payments-dash.jpg'],
    ['1559526324-4b87b5e36e44', 900, 500, 'fintech/mobile-pay.jpg'],
    ['1543286385-121b60d21f18', 900, 500, 'fintech/data-terminal.jpg'],
    ['1551288049-bebda4e38f71', 900, 500, 'fintech/kpi-dash.jpg'],
    ['1526304640581-d334cdbbf45e', 900, 500, 'fintech/currency.jpg'],
    ['1579621970563-ebec7560ff3e', 900, 500, 'fintech/wallet.jpg'],
    ['1507679799987-c73779587ccf', 900, 500, 'fintech/corporate.jpg'],
    ['1560472354-b33ff0c44a43', 900, 500, 'fintech/money-app.jpg'],
    ['1518186283189-7183d540c722', 900, 500, 'fintech/crypto.jpg'],
    ['1610375461246-83df859d849d', 900, 500, 'fintech/banking-app.jpg'],
    ['1611224923853-80b023f02d71', 900, 500, 'fintech/card-wallet.jpg'],
    ['1553729459-efe14ef6055d', 900, 500, 'fintech/phone-cash.jpg'],
    ['1567427017947-545c5f8d16ad', 900, 500, 'fintech/analytics-screen.jpg'],
    ['1516321318423-f06f85e504b3', 900, 500, 'fintech/ledger.jpg'],
    ['1444653614673-5d6c4b1e9611', 900, 500, 'fintech/charting.jpg'],
    ['1553729459-efe14ef6055d', 900, 500, 'fintech/cashphone.jpg'],
    ['1450101499163-c8848c66ca85', 900, 500, 'fintech/growth-deal.jpg'],
    ['1543286385-121b60d21f18', 900, 500, 'fintech/terminal.jpg'],
    ['1511512578047-dfb367046420', 900, 500, 'fintech/coins.jpg'],
  ],
  travel: [
    ['1506905925346-21bda4d32df4', 1200, 500, 'travel/hero-mountain.jpg'],
    ['1469474968028-56623f02e42e', 600, 400, 'travel/peak.jpg'],
    ['1507525428034-b723cf961d3e', 600, 400, 'travel/beach.jpg'],
    ['1519046904884-53103b34b206', 600, 400, 'travel/palm-beach.jpg'],
    ['1501785888041-af3ef285b470', 600, 400, 'travel/road.jpg'],
    ['1476514525535-07fb3b4ae5f1', 600, 400, 'travel/canoe.jpg'],
    ['1533105079780-92b9be482077', 600, 400, 'travel/hiker.jpg'],
    ['1519681393784-d120267933ba', 600, 400, 'travel/night-mtn.jpg'],
    ['1521295121783-8a321d551ad2', 600, 400, 'travel/alps.jpg'],
    ['1470071459604-3b5ec3a7fe05', 600, 400, 'travel/fog-forest.jpg'],
    ['1441974231531-c6227db76b6e', 600, 400, 'travel/forest.jpg'],
    ['1447752875215-b2761acb3c5d', 600, 400, 'travel/forest-rays.jpg'],
    ['1436491865332-7a61a109cc05', 800, 400, 'travel/plane.jpg'],
    ['1530521954074-e64f6810b32d', 600, 400, 'travel/map.jpg'],
    ['1500534314209-a157d0e14e17', 600, 400, 'travel/bridge.jpg'],
    ['1499856871958-5b9627545d1a', 600, 400, 'travel/temple.jpg'],
    ['1519682337058-a94d519337bc', 600, 400, 'travel/curves.jpg'],
    ['1506744038136-46273834b3fb', 600, 400, 'travel/coast.jpg'],
    ['1488646953014-85cb44e25828', 600, 400, 'travel/santorini.jpg'],
    ['1469854523086-cc02fe5d8800', 600, 400, 'travel/roadtrip.jpg'],
  ],
};

function download(url, dest, attempt = 1) {
  return new Promise((resolve) => {
    const dir = path.dirname(dest);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    if (fs.existsSync(dest) && fs.statSync(dest).size > 20000) { resolve('skip'); return; }

    const file = fs.createWriteStream(dest);
    const req = https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: 25000 }, (res) => {
      if ([301, 302, 303].includes(res.statusCode)) {
        file.close();
        fs.unlink(dest, () => {});
        download(res.headers.location, dest, attempt).then(resolve);
        return;
      }
      if (res.statusCode !== 200) {
        file.close(); fs.unlink(dest, () => {});
        // 429/5xx: retry with backoff
        if (attempt <= 3 && (res.statusCode === 429 || res.statusCode >= 500)) {
          setTimeout(() => download(url, dest, attempt + 1).then(resolve), attempt * 4000);
        } else {
          resolve(false);
        }
        return;
      }
      res.pipe(file);
      file.on('finish', () => {
        let st = { size: 0 };
        try { st = fs.statSync(dest); } catch { st = { size: 0 }; }
        if (st.size < 20000) { file.close(); fs.unlink(dest, () => {}); resolve(false); return; }
        const buf = fs.readFileSync(dest).subarray(0, 3);
        const isJpeg = buf[0] === 0xff && buf[1] === 0xd8;
        if (!isJpeg) { file.close(); fs.unlink(dest, () => {}); resolve(false); return; }
        file.close(); resolve(true);
      });
    });
    req.on('error', () => {
      file.close(); fs.unlink(dest, () => {});
      if (attempt <= 3) { setTimeout(() => download(url, dest, attempt + 1).then(resolve), attempt * 4000); }
      else { resolve(false); }
    });
    req.on('timeout', () => { req.destroy(); file.close(); fs.unlink(dest, () => {}); resolve(false); });
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const usedIds = new Set();
  let ok = 0, fail = 0;
  const failures = [];

  for (const [category, entries] of Object.entries(POOLS)) {
    let catOk = 0;
    for (const [id, w, h, rel] of entries) {
      if (usedIds.has(id)) { continue; }
      const url = `https://images.unsplash.com/photo-${id}?w=${w}&h=${h}&fit=crop&fm=jpg&q=80`;
      const dest = path.join(ROOT, 'src', 'assets', 'images', rel);
      const result = await download(url, dest);
      await sleep(180);
      usedIds.add(id);
      if (result === true) { catOk++; ok++; process.stdout.write(`✓ [${category}] ${rel}\n`); }
      else if (result === 'skip') { catOk++; ok++; }
      else { fail++; failures.push(rel); process.stdout.write(`✗ ${rel}\n`); }
    }
    const count = fs.existsSync(path.join(ROOT, 'src', 'assets', 'images', category))
      ? fs.readdirSync(path.join(ROOT, 'src', 'assets', 'images', category)).length : 0;
    console.log(`  → ${category}: ${count} files on disk (${catOk} this pass)`);
  }

  console.log(`\nDone: +${ok} files, ${fail} failed`);
  if (failures.length) {
    console.log('\nFAILED TARGETS (for retry):');
    failures.forEach((f) => console.log(`  ${f}`));
  }
}

main();
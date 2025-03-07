from mininet.topo import Topo


class AmlightTopo(Topo):
    """Amlight Topology."""

    def build(self):
        # Add switches
        self.Ampath1 = self.addSwitch(
            "Ampath1", listenPort=6601, dpid="0000000000000011"
        )
        self.Ampath2 = self.addSwitch(
            "Ampath2", listenPort=6602, dpid="0000000000000012"
        )
        SouthernLight2 = self.addSwitch(
            "SoL2", listenPort=6603, dpid="0000000000000013"
        )
        SanJuan = self.addSwitch("SanJuan", listenPort=6604, dpid="0000000000000014")
        AndesLight2 = self.addSwitch("AL2", listenPort=6605, dpid="0000000000000015")
        AndesLight3 = self.addSwitch("AL3", listenPort=6606, dpid="0000000000000016")
        self.Ampath3 = self.addSwitch(
            "Ampath3", listenPort=6608, dpid="0000000000000017"
        )
        self.Ampath4 = self.addSwitch(
            "Ampath4", listenPort=6609, dpid="0000000000000018"
        )
        self.Ampath5 = self.addSwitch(
            "Ampath5", listenPort=6610, dpid="0000000000000019"
        )
        self.Ampath7 = self.addSwitch(
            "Ampath7", listenPort=6611, dpid="0000000000000020"
        )
        JAX1 = self.addSwitch("JAX1", listenPort=6612, dpid="0000000000000021")
        JAX2 = self.addSwitch("JAX2", listenPort=6613, dpid="0000000000000022")
        # add hosts
        h1 = self.addHost("h1", mac="00:00:00:00:00:01")
        h2 = self.addHost("h2", mac="00:00:00:00:00:02")
        h3 = self.addHost("h3", mac="00:00:00:00:00:03")
        h4 = self.addHost("h4", mac="00:00:00:00:00:04")
        h5 = self.addHost("h5", mac="00:00:00:00:00:05")
        h6 = self.addHost("h6", mac="00:00:00:00:00:06")
        h7 = self.addHost("h7", mac="00:00:00:00:00:07")
        h8 = self.addHost("h8", mac="00:00:00:00:00:08")
        h9 = self.addHost("h9", mac="00:00:00:00:00:09")
        h10 = self.addHost("h10", mac="00:00:00:00:00:0A")
        h11 = self.addHost("h11", mac="00:00:00:00:00:0B")
        h12 = self.addHost("h12", mac="00:00:00:00:00:0C")
        h13 = self.addHost("h13", mac="00:00:00:00:00:0D")
        h14 = self.addHost("h14", mac="00:00:00:00:00:0E")
        h15 = self.addHost("h15", mac="00:00:00:00:00:0F")
        # Add links
        self.addLink(self.Ampath1, self.Ampath2, port1=1, port2=1)
        self.addLink(self.Ampath1, SouthernLight2, port1=2, port2=2)
        self.addLink(self.Ampath1, SouthernLight2, port1=3, port2=3)
        self.addLink(self.Ampath2, AndesLight2, port1=4, port2=4)
        self.addLink(SouthernLight2, AndesLight3, port1=5, port2=5)
        self.addLink(AndesLight3, AndesLight2, port1=6, port2=6)
        self.addLink(AndesLight2, SanJuan, port1=7, port2=7)
        self.addLink(SanJuan, self.Ampath2, port1=8, port2=8)
        self.addLink(self.Ampath1, self.Ampath3, port1=9, port2=9)
        self.addLink(self.Ampath2, self.Ampath3, port1=10, port2=10)
        self.addLink(self.Ampath1, self.Ampath4, port1=11, port2=11)
        self.addLink(self.Ampath2, self.Ampath5, port1=12, port2=12)
        self.addLink(self.Ampath4, self.Ampath5, port1=13, port2=13)
        self.addLink(self.Ampath4, JAX1, port1=14, port2=14)
        self.addLink(self.Ampath5, JAX2, port1=15, port2=15)
        self.addLink(self.Ampath4, self.Ampath7, port1=16, port2=16)
        self.addLink(self.Ampath7, SouthernLight2, port1=17, port2=17)
        self.addLink(JAX1, JAX2, port1=18, port2=18)
        self.addLink(h1, self.Ampath1, port1=1, port2=50)
        self.addLink(h2, self.Ampath2, port1=1, port2=51)
        self.addLink(h3, SouthernLight2, port1=1, port2=52)
        self.addLink(h4, SanJuan, port1=1, port2=53)
        self.addLink(h5, AndesLight2, port1=1, port2=54)
        self.addLink(h6, AndesLight3, port1=1, port2=55)
        self.addLink(h7, self.Ampath3, port1=1, port2=56)
        self.addLink(h8, self.Ampath4, port1=1, port2=57)
        self.addLink(h9, self.Ampath5, port1=1, port2=58)
        self.addLink(h10, self.Ampath7, port1=1, port2=59)
        self.addLink(h11, JAX1, port1=1, port2=60)
        self.addLink(h12, JAX2, port1=1, port2=61)
        self.addLink(h13, self.Ampath1, port1=1, port2=62)
        self.addLink(h14, self.Ampath2, port1=1, port2=63)
        self.addLink(h15, AndesLight2, port1=1, port2=64)


class AmlightLoopedTopo(AmlightTopo):
    """Amlight Topology with loops."""

    def build(self):
        super().build()
        # Add loops
        self.addLink(self.Ampath1, self.Ampath1, port1=17, port2=18)
        self.addLink(self.Ampath1, self.Ampath1, port1=19, port2=20)
        self.addLink(self.Ampath4, self.Ampath4, port1=25, port2=26)
        self.addLink(self.Ampath4, self.Ampath4, port1=9, port2=10)


topos = {
    "amlight": (lambda: AmlightTopo()),
    "amlight_looped": (lambda: AmlightLoopedTopo()),
}
